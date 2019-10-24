from typing import DefaultDict, OrderedDict, Optional, Sequence
from lft.consensus.events import (InitializeEvent, StartRoundEvent, DoneRoundEvent,
                                  ReceivedDataEvent, ReceivedVoteEvent)
from lft.consensus.data import Data, DataFactory
from lft.consensus.vote import Vote, VoteFactory
from lft.consensus.term import Term, TermFactory
from lft.consensus.layers.sync.sync_layer import SyncLayer
from lft.event import EventSystem, EventRegister
from lft.event.mediators import DelayedEventMediator

TIMEOUT_PROPOSE = 2.0
TIMEOUT_VOTE = 2.0

Datums = OrderedDict[bytes, Data]  # dict[data_id] = Data
Votes = DefaultDict[bytes, OrderedDict[bytes, Vote]]  # dict[voter_id][vote_id] = Vote


class AsyncLayer(EventRegister):
    def __init__(self,
                 sync_layer: SyncLayer,
                 node_id: bytes,
                 event_system: EventSystem,
                 data_factory: DataFactory,
                 vote_factory: VoteFactory,
                 term_factory: TermFactory):
        super().__init__(event_system.simulator)
        self._sync_layer = sync_layer
        self._node_id = node_id
        self._event_system = event_system
        self._data_factory = data_factory
        self._vote_factory = vote_factory
        self._term_factory = term_factory

        self._datums: Datums = OrderedDict()
        self._votes: Votes = DefaultDict(OrderedDict)

        self._term: Optional[Term] = None
        self._round_num = -1
        self._candidate_num = -1

        self._vote_timeout_started = False

    async def initialize(self,
                         term_num: int,
                         round_num: int,
                         candidate_data: Data,
                         votes: Sequence[Vote],
                         voters: Sequence[bytes]):
        candidate_num = candidate_data.number if candidate_data else 0
        self._candidate_num = candidate_num
        await self._new_round(term_num, round_num, voters)
        await self._new_data()
        await self._sync_layer.initialize(term_num, round_num, candidate_data, voters, votes)

    async def start_round(self,
                          term_num: int,
                          round_num: int,
                          voters: Sequence[bytes]):
        await self._new_round(term_num, round_num, voters)
        await self._new_data()
        await self._sync_layer.start_round(term_num, round_num, voters)

    async def done_round(self, candidate_data: Data):
        if candidate_data:
            self._candidate_num = candidate_data.number

    async def receive_data(self, data: Data):
        if not self._is_acceptable_data(data):
            return

        if self._candidate_num == data.number or self._candidate_num + 1 == data.number:
            if not data.is_not():
                self._term.verify_data(data)
            self._datums[data.id] = data
            await self._sync_layer.propose_data(data)

    async def receive_vote(self, vote: Vote):
        if not self._is_acceptable_vote(vote):
            return

        self._term.verify_vote(vote)
        self._votes[vote.voter_id][vote.id] = vote
        await self._sync_layer.vote_data(vote)

        if self._vote_timeout_started or not self._votes_reach_quorum():
            return
        self._vote_timeout_started = True
        for voter in self._term.get_voters_id():
            vote = await self._vote_factory.create_not_vote(voter, self._term.num, self._round_num)
            await self._raise_received_consensus_vote(delay=TIMEOUT_VOTE, vote=vote)

    async def _on_event_initialize(self, event: InitializeEvent):
        await self.initialize(event.term_num, event.round_num, event.candidate_data, event.votes, event.voters)

    async def _on_event_start_round(self, event: StartRoundEvent):
        await self.start_round(event.term_num, event.round_num, event.voters)

    async def _on_event_done_round(self, event: DoneRoundEvent):
        await self.done_round(event.candidate_data)

    async def _on_event_received_consensus_data(self, event: ReceivedDataEvent):
        await self.receive_data(event.data)

    async def _on_event_received_consensus_vote(self, event: ReceivedVoteEvent):
        await self.receive_vote(event.vote)

    async def _raise_received_consensus_data(self, delay: float, data: Data):
        event = ReceivedDataEvent(data)
        event.deterministic = False

        mediator = self._event_system.get_mediator(DelayedEventMediator)
        mediator.execute(delay, event)

    async def _raise_received_consensus_vote(self, delay: float, vote: Vote):
        event = ReceivedVoteEvent(vote)
        event.deterministic = False

        mediator = self._event_system.get_mediator(DelayedEventMediator)
        mediator.execute(delay, event)

    async def _new_round(self,
                         new_term_num: int,
                         new_round_num: int,
                         voters: Sequence[bytes] = ()):
        self._vote_timeout_started = False
        self._round_num = new_round_num
        self._datums.clear()
        self._votes.clear()

        if not self._term or self._term.num != new_term_num:
            self._term = self._term_factory.create_term(new_term_num, voters)

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
        if self._round_num != data.round_num:
            return False
        if self._candidate_num > data.number:
            return False
        if data.id in self._datums:
            return False
        if data.is_not() and self._datums:
            return False

        return True

    def _is_acceptable_vote(self, vote: Vote):
        if self._term.num != vote.term_num:
            return False
        if self._round_num != vote.round_num:
            return False
        if vote.id in self._votes[vote.voter_id]:
            return False
        if vote.is_not() and self._votes[vote.voter_id]:
            return False

        return True

    def _votes_reach_quorum(self):
        count = 0
        for voter_id, votes_by_id in self._votes.items():
            vote = next(iter(votes_by_id.values()), None)
            if vote and not vote.is_not():
                count += 1
        return count >= self._term.quorum_num

    _handler_prototypes = {
        InitializeEvent: _on_event_initialize,
        StartRoundEvent: _on_event_start_round,
        DoneRoundEvent: _on_event_done_round,
        ReceivedDataEvent: _on_event_received_consensus_data,
        ReceivedVoteEvent: _on_event_received_consensus_vote
    }
