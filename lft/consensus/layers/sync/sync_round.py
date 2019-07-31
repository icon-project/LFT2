from collections import defaultdict
from typing import Dict, Optional, Sequence, Set

from lft.consensus.factories import ConsensusData, ConsensusVote
from lft.consensus.term import Term


class SyncRound:
    def __init__(self,
                 term: Term,
                 round_num: int,
                 datas: Optional[Dict[bytes, ConsensusData]] = None,
                 votes: Optional[Sequence[ConsensusData]] = None):
        self.term: Term = term
        self.round_num: int = round_num

        self._datas: Dict[bytes, ConsensusData] = datas if datas else {}
        self._votes: ConsensusVotes = ConsensusVotes(votes)
        self.is_voted = False

    @property
    def term_num(self) -> int:
        return self.term.num

    def add_data(self, data: ConsensusData):
        self._datas[data.id] = data

    def add_vote(self, vote: ConsensusVote):
        self._votes.add_vote(vote)

    @property
    def is_complete(self) -> bool:
        if self.term.quorum_num <= self._votes.majority_vote_num:
            return True
        elif self.term.voters_num == self._votes.voter_num:
            return True
        return False


class ConsensusVotes:
    def __init__(self, votes: Optional[Sequence[ConsensusVote]] = None):
        self.majority_vote_num = 0
        self.majority_id = b''
        self._voters: Set[bytes] = ()
        self._votes: Dict[bytes, Dict[bytes, ConsensusVote]] = defaultdict(lambda: {})
        if votes:
            for vote in votes:
                self.add_vote(vote)

    def add_vote(self, vote: ConsensusVote):
        self._voters.add(vote.voter_id)
        self._votes[vote.data_id][vote.voter_id] = vote
        if len(self._votes[vote.data_id]) > self.majority_vote_num:
            self.majority_vote_num = len(self._votes[vote.data_id])
            self.majority_id = vote.data_id

    @property
    def voter_num(self) -> int:
        return len(self._voters)
