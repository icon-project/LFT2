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
from typing import Dict, Set, Sequence

from lft.app.data.consensus_votes import ConsensusVotes, EmptyVotes
from lft.consensus.data import ConsensusVote


class VoteCounter:
    def __init__(self):
        self._majority_id: bytes = b''
        self._votes: Dict[bytes, 'ConsensusVotes'] = {
            self._majority_id: EmptyVotes()
        }
        self._voters: Set[bytes] = set()

    @property
    def majority_id(self) -> bytes:
        return self._majority_id

    @property
    def majority_votes(self) -> ConsensusVotes:
        return self._votes[self._majority_id]

    @property
    def majority_counts(self) -> int:
        return len(self.majority_votes)

    @property
    def voter_counts(self) -> int:
        return len(self._voters)

    def add_vote(self, vote: ConsensusVote):
        if not vote.is_not():
            votes = self._votes.get(vote.data_id)
            if not votes:
                self._votes[vote.data_id] = ConsensusVotes(vote.data_id, vote.term_num, vote.round_num)
                votes = self._votes.get(vote.data_id)
            votes.add_vote(vote)
            self._update_majority(vote.data_id)
        self._voters.add(vote.voter_id)

    def _update_majority(self, data_id: bytes):
        if len(self._votes[data_id]) > self.majority_counts:
            self._majority_id = data_id
