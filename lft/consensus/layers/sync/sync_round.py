from dataclasses import dataclass
from typing import Dict, Optional, Sequence

from lft.consensus.data import Data, Vote
from lft.consensus.vote import VoteCounter
from lft.consensus.term import Term


@dataclass
class RoundResult:
    is_success: bool
    term_num: int
    round_num: int
    candidate_data: Optional[Data]
    votes: Sequence[Vote]


class SyncRound:
    _NOT_ID = b"Not"

    def __init__(self,
                 term: Term,
                 round_num: int,
                 datas: Optional[Dict[bytes, Data]] = None,
                 votes: Optional[Sequence[Vote]] = None):
        self.term: Term = term
        self.round_num: int = round_num

        self._datas: Dict[bytes, Data] = datas if datas else {}
        self._vote_counter: VoteCounter = VoteCounter()
        if votes:
            for vote in votes:
                self._vote_counter.add_vote(vote)
        self.is_voted = False
        self._apply = False

    @property
    def term_num(self) -> int:
        return self.term.num

    @property
    def is_apply(self) -> bool:
        return self._apply

    def apply(self):
        self._apply = True

    def add_data(self, data: Data):
        if data.is_not():
            self._datas[self._NOT_ID] = data
        else:
            self._datas[data.id] = data

    def add_vote(self, vote: Vote):
        self._vote_counter.add_vote(vote)

    def get_result(self) -> Optional[RoundResult]:
        if self._is_complete():
            if self._is_success():
                try:
                    candidate_data = self._datas[self._vote_counter.majority_id]
                except KeyError:
                    return None
                else:
                    return RoundResult(
                        is_success=True,
                        term_num=self.term_num,
                        round_num=self.round_num,
                        candidate_data=candidate_data,
                        votes=self._vote_counter.majority_votes.serialize(self.term.voters)
                    )
            else:
                # TODO: Fail Vote들도 알려줘야하나???
                return RoundResult(
                    is_success=False,
                    term_num=self.term_num,
                    round_num=self.round_num,
                    candidate_data=None,
                    votes=None
                )
        else:
            return None

    def _is_complete(self) -> bool:
        if self.term.quorum_num <= self._vote_counter.majority_counts:
            return True
        elif self.term.voters_num == self._vote_counter.voter_counts:
            return True
        elif self._vote_counter.voter_counts == self.term.voters_num - 1 and self._datas.get(self._NOT_ID):
            return True
        return False

    def _is_success(self) -> bool:
        if self._vote_counter.majority_counts >= self.term.quorum_num:
            if not self._vote_counter.majority_votes.is_none():
                return True
        return False
