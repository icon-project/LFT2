from typing import OrderedDict, DefaultDict, Sequence
from lft.consensus.candidate import Candidate
from lft.consensus.exceptions import (InvalidTerm, InvalidRound, AlreadyCandidate, AlreadySync,
                                      NeedSync, NotReachCandidate)
from lft.consensus.messages.data import Data
from lft.consensus.messages.vote import Vote
from lft.consensus.term import Term

Datums = DefaultDict[int, OrderedDict[int, OrderedDict[bytes, Data]]]
Votes = DefaultDict[int, DefaultDict[int, OrderedDict[bytes, Data]]]


class OrderMessages:
    def __init__(self, term: Term, candidate: Candidate):
        self._term: Term = term
        self._prev_term: Term = None
        self._candidate: Candidate = candidate
        self._datums = DefaultDict(OrderedDict)  # [round_num][data_id][data]
        self._votes = DefaultDict(lambda: DefaultDict(OrderedDict))  # [round_num][data_id][vote_id][vote]
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
