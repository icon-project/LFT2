from typing import OrderedDict, DefaultDict, Sequence, Optional, Dict
from lft.consensus.candidate import Candidate
from lft.consensus.exceptions import (InvalidTerm, InvalidRound, AlreadyCandidate, AlreadySync,
                                      NeedSync, NotReachCandidate)
from lft.consensus.messages.data import Data
from lft.consensus.messages.vote import Vote
from lft.consensus.term import Term

# [term_num][round_num][data_id][data]
Datums = DefaultDict[int, DefaultDict[int, OrderedDict[bytes, Data]]]
# [term_num][round_num][data_id][voter_id][vote]
Votes = DefaultDict[int, DefaultDict[int, DefaultDict[bytes, OrderedDict[bytes, Data]]]]


def _remove_past_messages(messages: Dict, now: int):
    for time in list(messages.keys()):
        if time < now:
            del messages[time]


class OrderMessages:
    def __init__(self, prev_term: Optional[Term], term: Term, candidate: Candidate):
        self._term: Term = term
        self._prev_term: Term = prev_term
        self._candidate: Candidate = candidate
        self._datums: Datums = DefaultDict(lambda: DefaultDict(OrderedDict))
        self._votes: Votes = DefaultDict(lambda : DefaultDict(lambda : DefaultDict(OrderedDict)))
        self._sync_request_datums = []

    @property
    def candidate(self) -> Candidate:
        return self._candidate

    @candidate.setter
    def candidate(self, candidate: Candidate):
        self._candidate = candidate
        _remove_past_messages(self._datums, candidate.data.term_num)
        _remove_past_messages(self._datums[candidate.data.term_num], candidate.data.round_num)
        _remove_past_messages(self._votes, candidate.data.term_num)
        _remove_past_messages(self._votes[candidate.data.term_num], candidate.data.round_num)

    @property
    def term(self) -> Term:
        return self._term

    def update_term(self, term: Term):
        if term != self._term:
            self._prev_term = self.term
            self._term = term

    def add_data(self, data: Data):
        self._datums[data.term_num][data.round_num][data.id] = data

    def add_vote(self, vote: Vote):
        self._votes[vote.term_num][vote.round_num][vote.data_id][vote.voter_id] = vote

    def get_reach_candidate(self, term_num: int, round_num: int, data_id: bytes) -> Candidate:
        verify_term = None
        if term_num == self._term.num:
            verify_term = self._term
        elif self._prev_term and term_num == self._prev_term.num:
            verify_term = self._prev_term
        else:
            raise InvalidTerm(term_num, self.term.num)

        if data_id == self.candidate.data.id:
            raise AlreadyCandidate

        same_data_id_votes = self._votes[term_num][round_num][data_id]

        if len(same_data_id_votes) >= verify_term.quorum_num:
            self._verify_missing_data(term_num, round_num, data_id)
            self._candidate = Candidate(self._datums[term_num][round_num][data_id], list(same_data_id_votes.values()))
            return self._candidate

        raise NotReachCandidate

    def get_datums(self, term_num: int, round_num: int) -> Sequence:
        return self._datums[term_num][round_num].values()

    def get_votes(self, term_num: int, round_num: int) -> Sequence:
        round_votes = []
        for votes_by_data_id in self._votes[term_num][round_num].values():
            round_votes.extend(votes_by_data_id.values())
        return round_votes

    def _verify_missing_data(self, term_num: int, round_num: int, data_id: bytes):
        try:
            data = self._datums[term_num][round_num][data_id]
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
