# -*- coding: utf-8 -*-

# Copyright 2019 ICON Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import List, Sequence

from lft.consensus.data import ConsensusVote


class ConsensusVotes:
    def __init__(self, data_id: bytes, term_num: int, round_num: int):
        self._data_id: bytes = data_id
        self._term_num: int = term_num
        self._round_num: int = round_num
        self._voters = set()
        self._votes: List['ConsensusVote'] = []

    @property
    def data_id(self) -> bytes:
        return self._data_id

    @property
    def term_num(self) -> int:
        return self._term_num

    @property
    def round_num(self) -> int:
        return self._round_num

    @property
    def votes(self) -> Sequence['ConsensusVote']:
        return self._votes

    def __len__(self):
        return len(self._votes)

    def add_vote(self, vote: 'ConsensusVote'):
        if vote.voter_id not in self._voters:
            if vote.data_id == self._data_id:
                self._votes.append(vote)
                self._voters.add(vote.voter_id)

    @classmethod
    def from_list(cls, consensus_votes: Sequence['ConsensusVote']) -> 'ConsensusVotes':
        new_object = cls(consensus_votes[0].data_id, consensus_votes[0].term_num, consensus_votes[0].round_num)
        for vote in consensus_votes:
            new_object.add_vote(vote)
        return new_object
