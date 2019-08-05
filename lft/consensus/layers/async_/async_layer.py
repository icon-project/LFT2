from collections import defaultdict
from typing import Dict, DefaultDict, OrderedDict, Optional, Sequence
from lft.consensus.events import (ReceivedConsensusDataEvent, ReceivedConsensusVoteEvent, ProposeSequence, VoteSequence,
                                  DoneRoundEvent, InitializeEvent)
from lft.consensus.data import ConsensusData, ConsensusDataFactory, ConsensusVote, ConsensusVoteFactory
from lft.consensus.term import Term, RotateTerm
from lft.event import EventSystem
from lft.event.mediators import DelayedEventMediator

TIMEOUT_PROPOSE = 2.0
TIMEOUT_VOTE = 2.0

DataByID = Dict[bytes, ConsensusData]  # dict[id] = ConsensusData
DataByRound = DefaultDict[int, DataByID]  # dict[round][id] = ConsensusData

VoteByID = OrderedDict[bytes, ConsensusVote]  # dict[id] = ConsensusVote
VoteByVoterID = DefaultDict[bytes, VoteByID]  # dict[voter_id][id] = ConsensusVote
VoteByRound = DefaultDict[int, VoteByVoterID]  # dict[round][voter_id][id] = ConsensusVote


class AsyncLayer:
    def __init__(self,
                 node_id: bytes,
                 event_system: EventSystem,
                 data_factory: ConsensusDataFactory,
                 vote_factory: ConsensusVoteFactory):
        self._node_id = node_id
        self._event_system = event_system
        self._data_factory = data_factory
        self._vote_factory = vote_factory

        self._data_dict: DataByRound = defaultdict(dict)
        self._vote_dict: VoteByRound = defaultdict(lambda: defaultdict(OrderedDict))
        self._term: Optional[Term] = None
        self._round_num = -1
        self._data_num = -1

        self._vote_timeout_started = False

        simulator = event_system.simulator
        self._handlers = {
            InitializeEvent:
                simulator.register_handler(InitializeEvent, self._on_event_initialize),
            DoneRoundEvent:
                simulator.register_handler(DoneRoundEvent, self._on_event_done_round),
            ReceivedConsensusDataEvent:
                simulator.register_handler(ReceivedConsensusDataEvent, self._on_event_received_consensus_data),
            ReceivedConsensusVoteEvent:
                simulator.register_handler(ReceivedConsensusVoteEvent, self._on_event_received_consensus_vote)
        }

    def __del__(self):
        self.close()

    def close(self):
        for event_type, handler in self._handlers.items():
            self._event_system.simulator.unregister_handler(event_type, handler)
        self._handlers.clear()

    async def _on_event_initialize(self, event: InitializeEvent):
        new_data_num = event.candidate_data.number + 1 if event.candidate_data else 0
        await self._new_round(new_data_num, event.term_num, event.round_num, event.voters)
        await self._new_data()

    async def _on_event_done_round(self, event: DoneRoundEvent):
        await self._new_round(event.candidate_data.number + 1, event.term_num, event.round_num + 1)
        await self._new_data()

    async def _on_event_received_consensus_data(self, event: ReceivedConsensusDataEvent):
        data = event.data
        if not self._is_acceptable_data(data):
            return

        if self._data_num == data.number:
            if self._round_num == data.round_num:
                if not data.is_not():
                    self._term.verify_data(data)
                self._data_dict[data.round_num][data.id] = data
                await self._raise_propose_sequence(data)
        elif self._data_num + 1 == data.number:
            if self._round_num + 1 == data.round_num:
                self._term.verify_data(data)
                self._data_dict[data.round_num][data.id] = data
                for vote in data.prev_votes:
                    await self._raise_received_consensus_vote(delay=0, vote=vote)
                await self._raise_received_consensus_data(delay=0, data=data)

    async def _on_event_received_consensus_vote(self, event: ReceivedConsensusVoteEvent):
        vote = event.vote
        if not self._is_acceptable_vote(vote):
            return

        self._term.verify_vote(vote)
        self._vote_dict[vote.round_num][vote.voter_id][vote.id] = vote

        if self._round_num != vote.round_num:
            return
        await self._raise_vote_sequence(vote)

        if self._vote_timeout_started or not self._votes_reach_quorum(self._round_num):
            return
        self._vote_timeout_started = True
        for voter in self._term.get_voters_id():
            vote = await self._vote_factory.create_not_vote(voter, self._term.num, self._round_num)
            await self._raise_received_consensus_vote(delay=TIMEOUT_VOTE, vote=vote)

    async def _raise_received_consensus_data(self, delay: float, data: ConsensusData):
        event = ReceivedConsensusDataEvent(data)
        event.deterministic = False

        mediator = self._event_system.get_mediator(DelayedEventMediator)
        mediator.execute(delay, event)

    async def _raise_received_consensus_vote(self, delay: float, vote: ConsensusVote):
        event = ReceivedConsensusVoteEvent(vote)
        event.deterministic = False

        mediator = self._event_system.get_mediator(DelayedEventMediator)
        mediator.execute(delay, event)

    async def _raise_propose_sequence(self, data: ConsensusData):
        propose_sequence = ProposeSequence(data)
        self._event_system.simulator.raise_event(propose_sequence)

    async def _raise_vote_sequence(self, vote: ConsensusVote):
        vote_sequence = VoteSequence(vote)
        self._event_system.simulator.raise_event(vote_sequence)

    async def _new_round(self,
                         new_data_num: int,
                         new_term_num: int,
                         new_round_num: int,
                         voters: Sequence[bytes] = ()):
        self._vote_timeout_started = False

        self._data_num = new_data_num
        self._round_num = new_round_num

        if not self._term or self._term.num != new_term_num:
            self._term = RotateTerm(new_term_num, voters)
            self._data_dict.clear()
            self._vote_dict.clear()
        else:
            self._trim_rounds(self._data_dict)
            self._trim_rounds(self._vote_dict)

            for data in self._data_dict[new_round_num]:
                await self._raise_received_consensus_data(delay=0, data=data)
            for votes in self._vote_dict[new_round_num]:
                for vote in votes:
                    await self._raise_received_consensus_vote(delay=0, vote=vote)

    async def _new_data(self):
        expected_proposer = self._term.get_proposer_id(self._round_num)
        if expected_proposer != self._node_id:
            data = await self._data_factory.create_not_data(self._data_num,
                                                            self._term.num,
                                                            self._round_num)
            await self._raise_received_consensus_data(delay=TIMEOUT_PROPOSE, data=data)

    def _is_acceptable_data(self, data: ConsensusData):
        if self._term.num != data.term_num:
            return False
        if self._round_num > data.round_num:
            return False
        if self._data_num > data.number:
            return False
        if data.id in self._data_dict[data.round_num]:
            return False
        if data.is_not() and self._data_dict[data.round_num]:
            return False

        return True

    def _is_acceptable_vote(self, vote: ConsensusVote):
        if self._term.num != vote.term_num:
            return False
        if self._round_num > vote.round_num:
            return False
        if vote.id in self._vote_dict[vote.round_num][vote.voter_id]:
            return False
        if vote.is_not() and self._vote_dict[vote.round_num][vote.voter_id]:
            return False

        return True

    def _votes_reach_quorum(self, round_num: int):
        count = 0
        for voter_id, votes_by_id in self._vote_dict[round_num].items():
            vote = next(iter(votes_by_id.values()), None)
            if vote and not vote.is_not():
                count += 1
        return count >= self._term.quorum_num

    def _trim_rounds(self, d: dict):
        expired_rounds = [round_ for round_ in d if round_ < self._round_num]
        for expired_round in expired_rounds:
            d.pop(expired_round, None)
