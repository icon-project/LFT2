import logging
from typing import DefaultDict, OrderedDict, Optional, Sequence
from lft.consensus.events import (InitializeEvent, StartRoundEvent, DoneRoundEvent,
                                  ReceivedDataEvent, ReceivedVoteEvent)
from lft.consensus.data import Data, DataFactory
from lft.consensus.vote import Vote, VoteFactory
from lft.consensus.term import Term, TermFactory
from lft.consensus.layers.round_layer import RoundLayer
from lft.consensus.exceptions import (InvalidRound, InvalidTerm, AlreadyProposed, AlreadyVoted,
                                      AlreadyDataReceived, AlreadyVoteReceived)
from lft.event import EventSystem, EventRegister
from lft.event.mediators import DelayedEventMediator

__all__ = ("SyncLayer",)

TIMEOUT_PROPOSE = 2.0
TIMEOUT_VOTE = 2.0


class SyncLayer(EventRegister):
    def __init__(self,
                 round_layer: RoundLayer,
                 node_id: bytes,
                 event_system: EventSystem,
                 data_factory: DataFactory,
                 vote_factory: VoteFactory,
                 term_factory: TermFactory):
        super().__init__(event_system.simulator)
        self._round_layer = round_layer
        self._node_id = node_id
        self._event_system = event_system
        self._data_factory = data_factory
        self._vote_factory = vote_factory
        self._term_factory = term_factory
        self._logger = logging.getLogger(node_id.hex())

        self._datums: Datums = Datums()
        self._votes: Votes = Votes()

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
        await self._round_layer.initialize(term_num, round_num, candidate_data, voters, votes)

    async def start_round(self,
                          term_num: int,
                          round_num: int,
                          voters: Sequence[bytes]):
        await self._new_round(term_num, round_num, voters)
        await self._new_data()
        await self._round_layer.start_round(term_num, round_num, voters)

    async def done_round(self, candidate_data: Data):
        if candidate_data:
            self._candidate_num = candidate_data.number

    async def receive_data(self, data: Data):
        try:
            await self._receive_data(data)
        except (InvalidTerm, InvalidRound, AlreadyProposed, AlreadyDataReceived):
            pass

    async def _receive_data(self, data: Data):
        self._verify_acceptable_data(data)

        if self._candidate_num == data.number or self._candidate_num + 1 == data.number:
            if not data.is_not():
                self._term.verify_data(data)
            self._datums[data.id] = data
            await self._round_layer.propose_data(data)

            if data.is_not():
                return

            votes_by_vote_id = self._votes.get_votes(data_id=data.id)
            for vote in votes_by_vote_id.values():
                await self._round_layer.vote_data(vote)

    async def receive_vote(self, vote: Vote):
        try:
            await self._receive_vote(vote)
        except (InvalidTerm, InvalidRound, AlreadyVoted, AlreadyVoteReceived):
            pass

    async def _receive_vote(self, vote: Vote):
        self._verify_acceptable_vote(vote)

        self._term.verify_vote(vote)
        self._votes.add_vote(vote)
        if vote.data_id in self._datums:
            await self._round_layer.vote_data(vote)

        if self._vote_timeout_started:
            return
        if not self._votes_reach_quorum():
            return
        if self._votes_reach_quorum_consensus():
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

    def _verify_acceptable_data(self, data: Data):
        if self._term.num != data.term_num:
            raise InvalidTerm(data.term_num, self._term.num)
        if self._round_num != data.round_num:
            raise InvalidRound(data.round_num, self._round_num)
        if self._candidate_num > data.number:  # This will be deleted
            return False
        if data.id in self._datums:
            raise AlreadyProposed(data.id, data.proposer_id)
        if data.is_not() and self._datums:
            raise AlreadyDataReceived

    def _verify_acceptable_vote(self, vote: Vote):
        if self._term.num != vote.term_num:
            raise InvalidTerm(vote.term_num, self._term.num)
        if self._round_num != vote.round_num:
            raise InvalidRound(vote.round_num, self._round_num)
        if vote.id in self._votes.get_votes(data_id=vote.data_id):
            raise AlreadyVoted(vote.id, vote.voter_id)
        if vote.is_not() and self._votes.get_votes(voter_id=vote.voter_id):
            raise AlreadyVoteReceived

    def _votes_reach_quorum(self):
        return sum(1 for vote in self._votes if not vote.is_not()) >= self._term.quorum_num

    def _votes_reach_quorum_consensus(self):
        def _first(values):
            return next(iter(values))

        return any(len(votes) >= self._term.quorum_num and not _first(votes.values()).is_not()
                   for votes in self._votes.votes_by_data_id.values())

    _handler_prototypes = {
        InitializeEvent: _on_event_initialize,
        StartRoundEvent: _on_event_start_round,
        DoneRoundEvent: _on_event_done_round,
        ReceivedDataEvent: _on_event_received_consensus_data,
        ReceivedVoteEvent: _on_event_received_consensus_vote
    }


Datums = OrderedDict[bytes, Data]


class Votes:
    def __init__(self):
        self.votes_by_data_id: DefaultDict[bytes, OrderedDict[Vote]] = DefaultDict(OrderedDict)
        self.votes_by_voter_id: DefaultDict[bytes, OrderedDict[Vote]] = DefaultDict(OrderedDict)

    def get_votes(self, *, data_id: Optional[bytes] = None, voter_id: Optional[bytes] = None):
        if data_id is not None and voter_id is None:
            return self.votes_by_data_id[data_id]
        if voter_id is not None and data_id is None:
            return self.votes_by_voter_id[voter_id]
        raise RuntimeError

    def add_vote(self, vote: Vote):
        self.votes_by_data_id[vote.data_id][vote.id] = vote
        self.votes_by_voter_id[vote.voter_id][vote.id] = vote

    def __iter__(self):
        for votes in self.votes_by_data_id.values():
            yield from votes.values()

    def clear(self):
        self.votes_by_data_id.clear()
        self.votes_by_voter_id.clear()

