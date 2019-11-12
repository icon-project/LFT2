import logging
from collections import defaultdict
from typing import Optional, Sequence, OrderedDict, Dict

from lft.consensus.round import Candidate
from lft.consensus.events import (InitializeEvent, RoundStartEvent, RoundEndEvent,
                                  ReceiveDataEvent, ReceiveVoteEvent, SyncRequestEvent)
from lft.consensus.exceptions import (InvalidTerm, InvalidRound, InvalidProposer, InvalidVoter,
                                      AlreadySync, AlreadyCandidate, NotReachCandidate,NeedSync)
from lft.consensus.layers import SyncLayer
from lft.consensus.term import Term
from lft.consensus.messages.data import DataFactory, Data
from lft.consensus.messages.vote import VoteFactory, Vote
from lft.event import EventRegister, EventSystem


class OrderLayer(EventRegister):
    def __init__(self,
                 sync_layer: SyncLayer,
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
        self._datums: Datums = defaultdict(lambda: defaultdict(OrderedDict))
        self._votes: Votes = defaultdict(lambda: defaultdict(OrderedDict))
        self._message_container: MessageContainer = None

        self._round_num = -1

    async def _on_event_initialize(self, event: InitializeEvent):
        await self._initialize(
            term=event.term,
            round_num=event.round_num,
            candidate_data=event.candidate_data,
            votes=event.votes
        )

    async def _on_event_round_start(self, event: RoundStartEvent):
        await self._round_start(event.term, event.round_num)

    async def _on_event_received_data(self, event: ReceiveDataEvent):
        try:
            await self._receive_data(event.data)
        except (InvalidTerm, InvalidRound, InvalidProposer, InvalidVoter, AlreadySync):
            pass

    async def _on_event_received_vote(self, event: ReceiveVoteEvent):
        try:
            await self._receive_vote(event.vote)
        except (InvalidTerm, InvalidRound, InvalidVoter, AlreadySync):
            pass

    async def _on_event_round_end(self, event: RoundEndEvent):
        if event.is_success:
            self._message_container.candidate = Candidate(event.candidate_data, event.candidate_votes)
            await self._sync_layer.round_end(event.candidate_data)

    async def _initialize(self, term: Term, round_num: int, candidate_data: Data, votes: Sequence['Vote']):
        self._term = term
        self._round_num = round_num
        candidate = Candidate(candidate_data, votes)
        self._message_container = MessageContainer(term, candidate)

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
        ReceiveDataEvent: _on_event_received_data,
        ReceiveVoteEvent: _on_event_received_vote,
        RoundEndEvent: _on_event_round_end
    }


Datums = Dict[int, Dict[int, OrderedDict[bytes, Data]]]
Votes = Dict[int, Dict[int, OrderedDict[bytes, Data]]]


class MessageContainer:
    def __init__(self, term: Term, candidate : Candidate):
        self._term: Term = term
        self._prev_term: Term = None
        self._candidate: Candidate = candidate
        self._datums = defaultdict(OrderedDict)  # [round_num][data_id][data]
        self._votes = defaultdict(lambda: defaultdict(OrderedDict))  # [round_num][data_id][vote_id][vote]
        self._sync_request_datums = []

    @property
    def candidate(self) -> Candidate:
        return self._candidate

    @candidate.setter
    def candidate(self, candidate: Candidate):
        self._candidate = candidate
        for round_num in list(self._datums.keys()):
            if round_num < candidate.data.round_num:
                del self._datums[round_num]

        for round_num in list(self._votes.keys()):
            if round_num < candidate.data.round_num:
                del self._votes[round_num]

    @property
    def term(self) -> Term:
        return self._term

    def update_term(self, term: Term):
        if term != self._term:
            self._prev_term = self.term
            self._term = term

    def add_data(self, data: Data):
        self._verify_acceptable_message(data)
        self._datums[data.round_num][data.id] = data

    def add_vote(self, vote: Vote):
        self._verify_acceptable_message(vote)
        self._votes[vote.round_num][vote.data_id][vote.voter_id] = vote

    def _verify_acceptable_message(self, message):
        if message.term_num == self.candidate.data.term_num:
            if message.round_num < self.candidate.data.round_num:
                raise InvalidRound(message.round_num, self.candidate.data.round_num)
        elif message.term_num < self.candidate.data.term_num:
            raise InvalidTerm(message.term_num, self.term.num)

    def get_reach_candidate(self, term_num: int, round_num: int, data_id: bytes) -> Candidate:
        if data_id == self.candidate.data.id:
            raise AlreadyCandidate

        same_data_id_votes = self._votes[round_num][data_id]

        if len(same_data_id_votes) >= self.term.quorum_num:
            self._verify_missing_data(term_num, round_num, data_id)
            self._candidate = Candidate(self._datums[round_num][data_id], list(same_data_id_votes.values()))
            return self._candidate

        raise NotReachCandidate

    def get_datums(self, round_num: int) -> Sequence:
        return self._datums[round_num].values()

    def get_votes(self, round_num: int) -> Sequence:
        round_votes = []
        for votes_by_data_id in self._votes[round_num].values():
            round_votes.extend(votes_by_data_id.values())
        return round_votes

    def _verify_missing_data(self, term_num: int, round_num: int, data_id: bytes):
        try:
            data = self._datums[round_num][data_id]
        except KeyError:
            self._raise_need_sync(data_id)
        else:
            if data.number != self.candidate.data.number and data.prev_id != self.candidate.data.id:
                self._raise_need_sync(data_id)

    def _raise_need_sync(self, data_id):
        if data_id not in self._sync_request_datums:
            self._sync_request_datums.append(data_id)
            raise NeedSync(self.candidate.data.id, data_id)
        else:
            raise AlreadySync(data_id)
