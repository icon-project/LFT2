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
from collections import defaultdict
from typing import Dict, Set, Sequence

from lft.consensus.data import ConsensusVote, ConsensusData


class VoteCounter:
    def __init__(self):
        self._votes: Dict[bytes, Dict[bytes, ConsensusVote]] = defaultdict(lambda: {})
        self._vote_counts: Dict[bytes, int] = defaultdict(lambda: 0)
        self._voters: Set[bytes] = set()
        self._majority_id: bytes = b''

    @property
    def majority_id(self) -> bytes:
        return self._majority_id

    @property
    def majority_votes(self) -> Sequence[ConsensusVote]:
        return list(self._votes[self._majority_id].values())

    @property
    def majority_counts(self) -> int:
        return self._vote_counts[self._majority_id]

    @property
    def voter_counts(self) -> int:
        return len(self._voters)

    @property
    def all_votes(self) -> Sequence[ConsensusVote]:
        all_votes = []
        for votes in self._votes.values():
            all_votes.extend(votes.values())
        return all_votes

    def add_vote(self, vote: ConsensusVote):
        if not vote.is_not():
            self._votes[vote.data_id][vote.voter_id] = vote
            self._vote_counts[vote.data_id] += 1
        self._voters.add(vote.voter_id)

        self._check_majority_is_change(vote.data_id)

    def inform_receive_data(self, data: ConsensusData):
        if data.is_not():
            return
        self._vote_counts[data.id] += 1
        self._voters.add(data.proposer_id)

        self._check_majority_is_change(data.id)

    def _check_majority_is_change(self, data_id: bytes):
        if self._vote_counts[data_id] > self.majority_counts:
            self._majority_id = data_id
