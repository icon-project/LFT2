from collections import defaultdict
from typing import List, Dict

from lft.consensus.factories import ConsensusData, ConsensusVote


class SyncRound:
    def __init__(self, term_num: int, round_num: int, datas, votes):
        self.term_num: int = term_num
        self.round_num: int = round_num

        self._datas: List[ConsensusData] = datas if datas else []
        self._votes: Dict[bytes][List[ConsensusVote]] = votes if votes else defaultdict(lambda: [])
        self.voted_data_id = None
        self.expired = False

    def add_data(self, data: ConsensusData):
        self._datas.append(data)

    def vote(self, vote: ConsensusVote):
        self.voted_data_id = vote.data_id
        self._votes[vote.data_id].append(vote)
