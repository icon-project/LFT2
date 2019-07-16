from collections import defaultdict
from typing import DefaultDict, Dict, Optional, Tuple
from lft.consensus.events import (ReceivedConsensusDataEvent, ReceivedConsensusVoteEvent, ProposeSequence, VoteSequence,
                                  QuorumEvent, InitializeEvent)
from lft.consensus.term import Term, RotateTerm
from lft.event import EventSystem
from lft.event.mediators import DelayedEventMediator
from lft.consensus.factories import ConsensusData, ConsensusDataFactory, ConsensusVote, ConsensusVoteFactory


TIMEOUT_PROPOSE = 2.0
TIMEOUT_VOTE = 2.0


class AsyncLayer:
    def __init__(self,
                 event_system: EventSystem,
                 data_factory: ConsensusDataFactory,
                 vote_factory: ConsensusVoteFactory):
        self._event_system = event_system
        self._data_factory = data_factory
        self._vote_factory = vote_factory

        self._data_dict: Dict[bytes, ConsensusData] = {}
        self._vote_dict: DefaultDict[bytes, Dict[bytes, ConsensusVote]] = defaultdict(dict)
        self._term: Optional[Term] = None
        self._round_num = -1

        self._handlers = [
            event_system.simulator.register_handler(InitializeEvent, self._on_event_initialize),
            event_system.simulator.register_handler(QuorumEvent, self._on_event_quorum),
            event_system.simulator.register_handler(ReceivedConsensusDataEvent, self._on_event_received_consensus_data),
            event_system.simulator.register_handler(ReceivedConsensusVoteEvent, self._on_event_received_consensus_vote)
        ]

    def __del__(self):
        self.close()

    def close(self):
        for handler in self._handlers:
            self._event_system.simulator.unregister_handler(handler)
        self._handlers.clear()

    async def _on_event_initialize(self, event: InitializeEvent):
        new_round_num = event.candidate_data.round_num + 1 if event.candidate_data else 0
        await self._new_round(new_round_num, event.voters)

    async def _on_event_quorum(self, event: QuorumEvent):
        await self._new_round(event.candidate_data.round_num + 1)

    async def _on_event_received_consensus_data(self, event: ReceivedConsensusDataEvent):
        data = event.data
        if not self._is_acceptable_data(data):
            return

        self._term.verify_data(data)
        if data.round_num == self._round_num:
            self._data_dict[data.id] = data
            await self._raise_propose_sequence(data)
            for voter in self._term.voters:
                await self._raise_received_consensus_vote(delay=TIMEOUT_VOTE, voter_id=voter)
        elif data.round_num == self._round_num + 1:
            for prev_vote in data.prev_votes:
                if prev_vote.voter_id not in self._term.voters:
                    continue
                if prev_vote.id in self._vote_dict[prev_vote.voter_id]:
                    continue
                self._vote_dict[prev_vote.voter_id][prev_vote.id] = prev_vote
                await self._raise_vote_sequence(prev_vote)
            await self._raise_received_consensus_data(0, data)

    async def _on_event_received_consensus_vote(self, event):
        vote = event.vote
        if not self._is_acceptable_vote(vote):
            return

        self._term.verify_vote(vote)
        self._vote_dict[vote.voter_id][vote.id] = vote
        await self._raise_vote_sequence(vote)

    async def _raise_received_consensus_data(self, delay: float, data: Optional[ConsensusData] = None):
        if data is None:
            data = await self._data_factory.create_not_data()

        event = ReceivedConsensusDataEvent(data)
        event.deterministic = False

        mediator = self._event_system.get_mediator(DelayedEventMediator)
        mediator.execute(delay, event)

    async def _raise_received_consensus_vote(self, delay: float, voter_id: bytes):
        vote = await self._vote_factory.create_not_vote(voter_id)

        event = ReceivedConsensusVoteEvent(vote)
        event.deterministic = False

        mediator = self._event_system.get_mediator(DelayedEventMediator)
        mediator.execute(delay, event)

    async def _raise_propose_sequence(self, data: ConsensusData):
        propose_sequence = ProposeSequence(data)
        self._event_system.simulator.raise_event(propose_sequence)

    async def _raise_vote_sequence(self, vote):
        vote_sequence = VoteSequence(vote)
        self._event_system.simulator.raise_event(vote_sequence)

    async def _new_round(self, new_round_num: int, voters: Tuple[bytes] = ()):
        self._round_num = new_round_num
        self._data_dict.clear()
        self._vote_dict.clear()

        if voters:
            self._term = RotateTerm(0, voters)
        await self._raise_received_consensus_data(delay=TIMEOUT_PROPOSE)

    def _is_acceptable_data(self, data: ConsensusData):
        if data.id in self._data_dict:
            return False
        if not data and self._data_dict:
            return False
        if data.term_num != self._term.num:
            return False
        if data.round_num < self._round_num:
            return False
        if data.round_num > self._round_num + 1:
            return False
        return True

    def _is_acceptable_vote(self, vote: ConsensusVote):
        if vote.id in self._vote_dict[vote.voter_id]:
            return False
        if not vote and self._vote_dict[vote.voter_id]:
            return False
        if vote.term_num != self._term.num:
            return False
        if vote.round_num != self._round_num:
            return False
        return True
