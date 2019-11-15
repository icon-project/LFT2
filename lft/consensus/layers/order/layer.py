import logging
from typing import Optional, Sequence, OrderedDict, TYPE_CHECKING

from lft.consensus.candidate import Candidate
from lft.consensus.events import (InitializeEvent, RoundStartEvent, RoundEndEvent,
                                  ReceiveDataEvent, ReceiveVoteEvent, SyncRequestEvent)
from lft.consensus.exceptions import (InvalidTerm, InvalidRound, InvalidProposer, InvalidVoter,
                                      AlreadySync, AlreadyCandidate, NotReachCandidate,NeedSync)
from lft.consensus.layers.order import OrderMessages
from lft.consensus.term import Term
from lft.consensus.messages.data import DataFactory, Data
from lft.consensus.messages.vote import VoteFactory, Vote
from lft.event import EventRegister, EventSystem


if TYPE_CHECKING:
    from lft.consensus.layers.sync import SyncLayer


class OrderLayer(EventRegister):
    def __init__(self,
                 sync_layer: 'SyncLayer',
                 node_id: bytes,
                 event_system: EventSystem,
                 data_factory: DataFactory,
                 vote_factory: VoteFactory):
        super().__init__(event_system.simulator)
        self._sync_layer = sync_layer
        self._node_id = node_id
        self._event_system = event_system
        self._data_factory = data_factory
        self._vote_factory = vote_factory
        self._logger = logging.getLogger(node_id.hex())

        self._term: Optional[Term] = None
        self._prev_term: Optional[Term] = None
        self._round_num = -1
        self._message_container: OrderMessages = None

    async def _on_event_initialize(self, event: InitializeEvent):
        await self._initialize(
            prev_term=event.term,
            term=event.term,
            round_num=event.round_num,
            candidate_data=event.candidate_data,
            votes=event.votes
        )

    async def _on_event_round_start(self, event: RoundStartEvent):
        await self._round_start(event.term, event.round_num)

    async def _on_event_receive_data(self, event: ReceiveDataEvent):
        try:
            await self._receive_data(event.data)
        except (InvalidTerm, InvalidRound, InvalidProposer, InvalidVoter, AlreadySync):
            pass

    async def _on_event_receive_vote(self, event: ReceiveVoteEvent):
        try:
            await self._receive_vote(event.vote)
        except (InvalidTerm, InvalidRound, InvalidVoter, AlreadySync):
            pass

    async def _on_event_round_end(self, event: RoundEndEvent):
        if event.is_success:
            self._message_container.candidate = Candidate(event.candidate_data, event.candidate_votes)

    async def _initialize(self, prev_term: Optional[Term], term: Term, round_num: int,
                          candidate_data: Data, votes: Sequence['Vote']):
        self._prev_term = prev_term
        self._term = term
        self._round_num = round_num
        candidate = Candidate(candidate_data, votes)
        self._message_container = OrderMessages(term, candidate)

        await self._sync_layer.initialize(term, round_num, candidate_data, votes)

    async def _round_start(self, term: Term, round_num: int):
        self._verify_acceptable_round_start(term, round_num)

        self._term = term
        self._round_num = round_num
        await self._sync_layer.round_start(term, round_num)

        for data in self._get_datums(self._round_num):
            await self._sync_layer.receive_data(data)

        for vote in self._get_votes(self._round_num):
            await self._sync_layer.receive_vote(vote)

    async def _receive_data(self, data: Data):
        self._verify_acceptable_data(data)
        self._save_data(data)
        sample_vote = self._save_votes_and_get_sample(data)
        if self._is_now_round_message(data):
            await self._sync_layer.receive_data(data)
        if sample_vote:
            await self._change_candidate_if_reach(sample_vote.term_num, sample_vote.round_num, sample_vote.data_id)

    def _save_votes_and_get_sample(self, data):
        sample_vote = None
        for vote in data.prev_votes:
            if isinstance(vote, Vote):
                if not sample_vote:
                    sample_vote = vote
                self._save_vote(vote)
        return sample_vote

    async def _receive_vote(self, vote: Vote):
        self._verify_acceptable_vote(vote)
        self._save_vote(vote)
        if self._is_now_round_message(vote):
            await self._sync_layer.receive_vote(vote)
        else:
            await self._change_candidate_if_reach(vote.term_num, vote.round_num, vote.data_id)

    async def _change_candidate_if_reach(self, term_num: int, round_num: int, data_id: bytes):
        try:
            candidate = self._message_container.get_reach_candidate(term_num, round_num, data_id)
        except NeedSync as e:
            self._event_system.simulator.raise_event(
                SyncRequestEvent(e.old_candidate_id, e.new_candidate_id)
            )
        except (AlreadyCandidate, NotReachCandidate):
            pass
        else:
            if self._round_num < candidate.data.round_num:
                self._round_num = candidate.data.round_num
            await self._sync_layer.change_candidate(candidate)

    def _is_now_round_message(self, message):
        return message.round_num == self._round_num

    def _verify_acceptable_round_start(self, term: Term, round_num: int):
        if term.num == self._term.num:
            if round_num != self._round_num + 1:
                raise InvalidRound(round_num, self._round_num)
        elif term.num == self._term.num + 1:
            if round_num != 0:
                raise InvalidRound(round_num, 0)
        else:
            raise InvalidTerm(term=term.num, expected=self._term.num)

    def _verify_acceptable_data(self, data: Data):
        self._verify_acceptable_round_message(data)
        # TODO Term verify data
        if self._term.verify_proposer(data.proposer_id, data.round_num):
            raise InvalidProposer(data.proposer_id, self._term.get_proposer_id(data.round_num))

    def _verify_acceptable_round_message(self, message):
        if message.term_num != self._term.num:
            raise InvalidTerm(message.term_num, self._term.num)
        elif message.round_num < self._message_container.candidate.data.round_num:
            if message.term_num == self._message_container.candidate.data.term_num:
                raise InvalidRound(message.round_num, self._round_num)

    def _verify_acceptable_vote(self, vote: Vote):
        self._verify_acceptable_round_message(vote)
        if not (vote.voter_id in self._term.voters):
            raise InvalidVoter(vote.voter_id, b'')

    def _save_data(self, data: Data):
        self._message_container.add_data(data)

    def _save_vote(self, vote: Vote):
        self._message_container.add_vote(vote)

    def _get_datums(self, round_num: int) -> Sequence:
        return self._message_container.get_datums(round_num)

    def _get_votes(self, round_num: int) -> Sequence:
        return self._message_container.get_votes(round_num)

    _handler_prototypes = {
        InitializeEvent: _on_event_initialize,
        RoundStartEvent: _on_event_round_start,
        ReceiveDataEvent: _on_event_receive_data,
        ReceiveVoteEvent: _on_event_receive_vote,
        RoundEndEvent: _on_event_round_end
    }
