from collections import defaultdict
from typing import Dict, Optional

from lft.consensus.factories import ConsensusData, ConsensusVote


class SyncRound:
    def __init__(self,
                 term_num: int,
                 round_num: int,
                 datas: Optional[Dict[bytes, ConsensusData]] = None,
                 votes: Optional[Dict[bytes, ConsensusData]] = None):
        self.term_num: int = term_num
        self.round_num: int = round_num

        self._datas: Dict[bytes, ConsensusData] = datas if datas else {}
        self._votes: Dict[bytes, Dict[bytes, ConsensusVote]] = votes if votes else defaultdict(lambda: {})
        self.is_voted = False

    def add_data(self, data: ConsensusData):
        self._datas[data.id] = data

    def add_vote(self, vote: ConsensusVote):
        self.voted_data_id = vote.data_id
        self._votes[vote.data_id][vote.voter_id] = vote
