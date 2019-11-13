import logging
from typing import OrderedDict, Optional, Sequence, TYPE_CHECKING
from lft.consensus.messages.data import Data, DataFactory
from lft.consensus.messages.vote import Vote, VoteFactory
from lft.consensus.candidate import Candidate
from lft.consensus.events import ReceiveDataEvent, ReceiveVoteEvent
from lft.consensus.term import Term
from lft.consensus.layers.sync import SyncMessages
from lft.consensus.exceptions import (InvalidRound, InvalidTerm, AlreadyProposed, AlreadyVoted,
                                      AlreadyDataReceived, AlreadyVoteReceived)
from lft.event import EventSystem
from lft.event.mediators import DelayedEventMediator


if TYPE_CHECKING:
    from lft.consensus.layers.round import RoundLayer

__all__ = ("SyncLayer",)

TIMEOUT_PROPOSE = 2.0
TIMEOUT_VOTE = 2.0


class SyncLayer:
    def __init__(self,
                 round_layer: 'RoundLayer',
                 node_id: bytes,
                 event_system: EventSystem,
                 data_factory: DataFactory,
                 vote_factory: VoteFactory):
        self._round_layer = round_layer
        self._node_id = node_id
        self._event_system = event_system
        self._data_factory = data_factory
        self._vote_factory = vote_factory
        self._logger = logging.getLogger(node_id.hex())

        self._term: Optional[Term] = None
        self._round_num = -1
        self._candidate_num = -1

        self._messages: Optional[SyncMessages] = None
        self._vote_timeout_started = False

    async def initialize(self,
                         term: Term,
                         round_num: int,
                         candidate_data: Data,
                         votes: Sequence[Vote]):
        candidate_num = candidate_data.number if candidate_data else 0
        self._candidate_num = candidate_num
        await self._new_round(term, round_num)
        await self._new_data()
        await self._round_layer.initialize(term, round_num, candidate_data, votes)

    async def round_start(self,
                          term: Term,
                          round_num: int):
        await self._new_round(term, round_num)
        await self._new_data()
        await self._round_layer.round_start(term, round_num)

    async def round_end(self, candidate_data: Data):
        if candidate_data:
            self._candidate_num = candidate_data.number

    async def receive_data(self, data: Data):
        try:
            await self._receive_data(data)
        except (InvalidTerm, InvalidRound, AlreadyProposed, AlreadyDataReceived):
            pass

    async def _receive_data(self, data: Data):
        self._verify_acceptable_data(data)

        self._messages.add_data(data)
        await self._round_layer.propose_data(data)

        if data.is_not():
            return

        votes_by_data_id = self._messages.get_votes(data_id=data.id)
        for vote in votes_by_data_id.values():
            await self._round_layer.vote_data(vote)

    async def receive_vote(self, vote: Vote):
        try:
            await self._receive_vote(vote)
        except (InvalidTerm, InvalidRound, AlreadyVoted, AlreadyVoteReceived):
            pass

    async def _receive_vote(self, vote: Vote):
        self._verify_acceptable_vote(vote)

        self._messages.add_vote(vote)
        if vote.is_none() or self._messages.get_data(vote.data_id):
            await self._round_layer.vote_data(vote)

        if self._vote_timeout_started:
            return
        if not self._messages.reach_quorum(self._term.quorum_num):
            return
        if self._messages.reach_quorum_consensus(self._term.quorum_num):
            return

        self._vote_timeout_started = True
        for voter in self._term.get_voters_id():
            vote = await self._vote_factory.create_not_vote(voter, self._term.num, self._round_num)
            await self._raise_received_consensus_vote(delay=TIMEOUT_VOTE, vote=vote)

    async def change_candidate(self, candidate: Candidate):
        self._candidate_num = candidate.data.number
        if self._term.num == candidate.data.term_num:
            if self._round_num < candidate.data.round_num:
                await self._new_round(self._term, candidate.data.round_num)
                await self._new_data()
        await self._round_layer.change_candidate(candidate)

    async def _raise_received_consensus_data(self, delay: float, data: Data):
        event = ReceiveDataEvent(data)
        event.deterministic = False

        mediator = self._event_system.get_mediator(DelayedEventMediator)
        mediator.execute(delay, event)

    async def _raise_received_consensus_vote(self, delay: float, vote: Vote):
        event = ReceiveVoteEvent(vote)
        event.deterministic = False

        mediator = self._event_system.get_mediator(DelayedEventMediator)
        mediator.execute(delay, event)

    async def _new_round(self,
                         new_term: Term,
                         new_round_num: int):
        self._vote_timeout_started = False
        self._term = new_term
        self._round_num = new_round_num
        self._messages = SyncMessages()

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
        if data in self._messages:
            raise AlreadyProposed(data.id, data.proposer_id)
        if data.is_not() and self._messages.datums:
            raise AlreadyDataReceived

    def _verify_acceptable_vote(self, vote: Vote):
        if self._term.num != vote.term_num:
            raise InvalidTerm(vote.term_num, self._term.num)
        if self._round_num != vote.round_num:
            raise InvalidRound(vote.round_num, self._round_num)
        if vote in self._messages:
            raise AlreadyVoted(vote.id, vote.voter_id)
        if vote.is_not() and self._messages.votes:
            raise AlreadyVoteReceived
