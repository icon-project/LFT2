from dataclasses import dataclass
from typing import Dict, Optional, Sequence

from lft.consensus.data import ConsensusData, ConsensusVote
from lft.consensus.term import Term
from lft.consensus.vote_counter import VoteCounter


@dataclass
class RoundResult:
    is_success: bool
    term_num: int
    round_num: int
    candidate_data: Optional[ConsensusData]
    votes: Sequence[ConsensusVote]


class SyncRound:
    _NOT_ID = b"Not"

    def __init__(self,
                 term: Term,
                 round_num: int,
                 datas: Optional[Dict[bytes, ConsensusData]] = None,
                 votes: Optional[Sequence[ConsensusVote]] = None):
        self.term: Term = term
        self.round_num: int = round_num

        self._datas: Dict[bytes, ConsensusData] = datas if datas else {}
        self._votes: VoteCounter = VoteCounter()
        if votes:
            for vote in votes:
                self._votes.add_vote(vote)
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

    def add_data(self, data: ConsensusData):
        if data.is_not():
            self._datas[self._NOT_ID] = data
        else:
            self._datas[data.id] = data

    def add_vote(self, vote: ConsensusVote):
        self._votes.add_vote(vote)

    def get_result(self) -> Optional[RoundResult]:
        if self._is_complete():
            if self._is_success():
                return RoundResult(
                    is_success=True,
                    term_num=self.term_num,
                    round_num=self.round_num,
                    candidate_data=self._datas[self._votes.majority_id],
                    votes=self._votes.majority_votes.serialize(self.term.voters)
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
        if self.term.quorum_num <= self._votes.majority_counts:
            return True
        elif self.term.voters_num == self._votes.voter_counts:
            return True
        elif self._votes.voter_counts == self.term.voters_num - 1 and self._datas.get(self._NOT_ID):
            return True
        return False

    def _is_success(self) -> bool:
        if self._votes.majority_counts >= self.term.quorum_num:
            if not self._votes.majority_votes.is_none()
                return True
        return False
