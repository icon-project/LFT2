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

from lft.app.data.consensus_votes import ConsensusVotes
from lft.consensus.data import ConsensusVote, ConsensusData


class VoteCounter:
    def __init__(self):
        self._votes: Dict[bytes, 'ConsensusVotes'] = PramsDefaultDict(ConsensusVotes)
        self._voters: Set[bytes] = set()
        self._majority_id: bytes = b''

    @property
    def majority_id(self) -> bytes:
        return self._majority_id

    @property
    def majority_votes(self) -> Sequence['ConsensusVote']:
        return self._votes[self._majority_id].votes

    @property
    def majority_counts(self) -> int:
        return len(self._votes[self._majority_id])

    @property
    def voter_counts(self) -> int:
        return len(self._voters)

    @property
    def all_votes(self) -> Sequence['ConsensusVote']:
        all_votes = []
        for votes_by_data_id in self._votes.values():
            all_votes.extend(votes_by_data_id.votes)
        return all_votes

    def add_vote(self, vote: ConsensusVote):
        if not vote.is_not():
            self._votes[vote.data_id].add_vote(vote)
        self._voters.add(vote.voter_id)
        self._update_majority(vote.data_id)

    def _update_majority(self, data_id: bytes):
        if len(self._votes[data_id]) > self.majority_counts:
            self._majority_id = data_id


class PramsDefaultDict(defaultdict):
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        else:
            ret = self[key] = self.default_factory(key)
            return ret
