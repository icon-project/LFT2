from collections import defaultdict
from typing import Dict, DefaultDict, OrderedDict, Optional, Sequence
from lft.consensus.events import (ReceivedDataEvent, ReceivedVoteEvent, ProposeSequence, VoteSequence,
                                  DoneRoundEvent, InitializeEvent, StartRoundEvent)
from lft.consensus.data import Data, DataFactory
from lft.consensus.vote import Vote, VoteFactory
from lft.consensus.term import Term, TermFactory
from lft.event import EventSystem, EventRegister
from lft.event.mediators import DelayedEventMediator

TIMEOUT_PROPOSE = 2.0
TIMEOUT_VOTE = 2.0

DataByID = Dict[bytes, Data]  # dict[id] = Data
DataByRound = DefaultDict[int, DataByID]  # dict[round][id] = Data

VoteByID = OrderedDict[bytes, Vote]  # dict[id] = Vote
VoteByVoterID = DefaultDict[bytes, VoteByID]  # dict[voter_id][id] = Vote
VoteByRound = DefaultDict[int, VoteByVoterID]  # dict[round][voter_id][id] = Vote


class AsyncLayer(EventRegister):
    def __init__(self,
                 node_id: bytes,
                 event_system: EventSystem,
                 data_factory: DataFactory,
                 vote_factory: VoteFactory,
                 term_factory: TermFactory):
        super().__init__(event_system.simulator)
        self._node_id = node_id
        self._event_system = event_system
        self._data_factory = data_factory
        self._vote_factory = vote_factory
        self._term_factory = term_factory

        self._data_dict: DataByRound = defaultdict(dict)
        self._vote_dict: VoteByRound = defaultdict(lambda: defaultdict(OrderedDict))
        self._term: Optional[Term] = None
        self._round_num = -1
        self._candidate_num = -1

        self._vote_timeout_started = False

    async def _on_event_initialize(self, event: InitializeEvent):
        candidate_num = event.candidate_data.number if event.candidate_data else 0
        self._candidate_num = candidate_num
        await self._new_round(event.term_num, event.round_num, event.voters)
        await self._new_data()

    async def _on_event_start_round(self, event: StartRoundEvent):
        await self._new_round(event.term_num, event.round_num, event.voters)
        await self._new_data()

    async def _on_event_done_round(self, event: DoneRoundEvent):
        if event.candidate_data:
            self._candidate_num = event.candidate_data.number

    async def _on_event_received_consensus_data(self, event: ReceivedDataEvent):

        data = event.data
        if not self._is_acceptable_data(data):
            return

        if self._candidate_num == data.number or self._candidate_num + 1 == data.number:
            if self._round_num == data.round_num:
                if not data.is_not():
                    self._term.verify_data(data)
                self._data_dict[data.round_num][data.id] = data
                await self._raise_propose_sequence(data)
        elif self._candidate_num + 2 == data.number:
            if self._round_num + 1 == data.round_num:
                self._term.verify_data(data)
                self._data_dict[data.round_num][data.id] = data
                for vote in data.prev_votes:
                    await self._raise_received_consensus_vote(delay=0, vote=vote)
                await self._raise_received_consensus_data(delay=0, data=data)

    async def _on_event_received_consensus_vote(self, event: ReceivedVoteEvent):
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

    async def _raise_received_consensus_data(self, delay: float, data: Data):
        event = ReceivedDataEvent(data)

        event.deterministic = False

        mediator = self._event_system.get_mediator(DelayedEventMediator)
        mediator.execute(delay, event)

    async def _raise_received_consensus_vote(self, delay: float, vote: Vote):
        if isinstance(vote, Vote):
            event = ReceivedVoteEvent(vote)
            event.deterministic = False

            mediator = self._event_system.get_mediator(DelayedEventMediator)
            mediator.execute(delay, event)

    async def _raise_propose_sequence(self, data: Data):
        propose_sequence = ProposeSequence(data)
        self._event_system.simulator.raise_event(propose_sequence)

    async def _raise_vote_sequence(self, vote: Vote):
        vote_sequence = VoteSequence(vote)
        self._event_system.simulator.raise_event(vote_sequence)

    async def _new_round(self,
                         new_term_num: int,
                         new_round_num: int,
                         voters: Sequence[bytes] = ()):
        self._vote_timeout_started = False

        self._round_num = new_round_num

        if not self._term or self._term.num != new_term_num:
            self._term = self._term_factory.create_term(new_term_num, voters)
            self._data_dict.clear()
            self._vote_dict.clear()
        else:
            self._trim_rounds(self._data_dict)
            self._trim_rounds(self._vote_dict)

            for data in self._data_dict[new_round_num].values():
                await self._raise_received_consensus_data(delay=0, data=data)
            for votes in self._vote_dict[new_round_num].values():
                for vote in votes:
                    print(vote)
                    await self._raise_received_consensus_vote(delay=0, vote=vote)

    async def _new_data(self):
        expected_proposer = self._term.get_proposer_id(self._round_num)
        if expected_proposer != self._node_id:
            data = await self._data_factory.create_not_data(self._candidate_num,
                                                            self._term.num,
                                                            self._round_num,
                                                            expected_proposer)
            await self._raise_received_consensus_data(delay=TIMEOUT_PROPOSE, data=data)

    def _is_acceptable_data(self, data: Data):
        if self._term.num != data.term_num:
            return False
        if self._round_num > data.round_num:
            return False
        if self._candidate_num > data.number:
            return False
        if data.id in self._data_dict[data.round_num]:
            return False
        if data.is_not() and self._data_dict[data.round_num]:
            return False

        return True

    def _is_acceptable_vote(self, vote: Vote):
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

    _handler_prototypes = {
        InitializeEvent: _on_event_initialize,
        StartRoundEvent: _on_event_start_round,
        DoneRoundEvent: _on_event_done_round,
        ReceivedDataEvent: _on_event_received_consensus_data,
        ReceivedVoteEvent: _on_event_received_consensus_vote
    }
