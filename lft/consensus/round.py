from typing import List, Dict, DefaultDict, Set, Sequence, Optional, NamedTuple
from lft.consensus.messages.data import Data, Vote
from lft.consensus.term import Term
from lft.consensus.exceptions import CannotComplete, AlreadyCompleted, AlreadyVoted, NotCompleted, DataIDNotFound

Datums = Dict[bytes, Data]  # dict[data_id] = data
Votes = DefaultDict[bytes, List[Vote]]  # dict[data_id][0] = vote

Candidate = NamedTuple("Candidate", [("data", Optional[Data]), ("votes", Sequence[Vote])])


class Round:
    def __init__(self, num: int, term: Term):
        self.num = num
        self.term = term

        self._datums: Datums = {}
        self._votes: Votes = DefaultDict(list)
        self._voters: Set[bytes] = set()

        self._is_completed = False

    @property
    def is_completed(self):
        return self._is_completed

    def add_data(self, data: Data):
        if self.is_completed:
            raise AlreadyCompleted

        self._datums[data.id] = data

    def add_vote(self, vote: Vote):
        if self.is_completed:
            raise AlreadyCompleted

        if vote.voter_id in self._voters:
            raise AlreadyVoted(vote.id, vote.voter_id)

        self._voters.add(vote.voter_id)
        self._votes[vote.data_id].append(vote)

    def complete(self):
        if self.is_completed:
            raise AlreadyCompleted

        try:
            max_data_id = self._find_max_data_id()
        except ValueError:
            raise CannotComplete(f"Datums is empty. {self._datums}")

        majority = len(self._votes[max_data_id])
        if self.term.quorum_num > majority and self.term.voters_num != len(self._voters):
            raise CannotComplete(f"Majority({majority}) does not reach quorum({self.term.quorum_num} or "
                                 f"All voters have not voted. ({len(self._voters)}/{self.term.voters_num})")

        vote = self._votes[max_data_id][0]
        if not vote.is_not() and not vote.is_none():
            if max_data_id not in self._datums:
                raise DataIDNotFound(f"Upper layers did not send data. {max_data_id}")

        self._is_completed = True

    def result(self):
        if not self.is_completed:
            raise NotCompleted

        candidate_data_id = self._find_max_data_id()

        unordered_votes = self._votes[candidate_data_id]
        candidate_votes = self._order_votes(unordered_votes)

        vote = unordered_votes[0]
        if vote.is_none() or vote.is_not():
            return Candidate(None, candidate_votes)

        if self.term.quorum_num > len(unordered_votes):
            return Candidate(None, candidate_votes)
        try:
            candidate_data = self._datums[candidate_data_id]
        except KeyError:
            raise DataIDNotFound
        else:
            return Candidate(candidate_data, candidate_votes)

    def _find_max_data_id(self):
        return max(self._votes, key=lambda key: len(self._votes.get(key)))

    def _order_votes(self, votes: List[Vote]):
        ordered_votes = []
        for voter in self.term.voters:
            ordered_vote = next((vote for vote in votes if vote.voter_id == voter), None)
            ordered_votes.append(ordered_vote)
        return ordered_votes


