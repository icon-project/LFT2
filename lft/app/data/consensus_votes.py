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
from typing import List, Sequence, Type, TypeVar

from lft.consensus.data import ConsensusVote

T = TypeVar("T")


class ConsensusVotes:
    def __init__(self, data_id: bytes, term_num: int, round_num: int):
        self._data_id: bytes = data_id
        self._term_num: int = term_num
        self._round_num: int = round_num
        self._voters = set()
        self._votes: List['ConsensusVote'] = []
        self._is_none = None

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
                if self._is_none is None:
                    self._is_none = True if vote.is_none() else False
                self._votes.append(vote)
                self._voters.add(vote.voter_id)

    def serialize(self, voters: Sequence[bytes]) -> List:
        votes = [b'' for x in voters]
        for vote in self._votes:
            try:
                vote_index = voters.index(vote.voter_id)
            except ValueError as e:
                print(f"Unknown voter : {vote.voter_id}")
            else:
                votes[vote_index] = vote
        return votes

    @classmethod
    def deserialize(cls: Type[T], votes: Sequence) -> T:
        deserialized_obj = None
        print(f"deserialize votes {votes} ")
        for vote in votes:
            if isinstance(vote, ConsensusVote):
                if not deserialized_obj:
                    deserialized_obj = cls(data_id=vote.data_id,
                                           term_num=vote.term_num,
                                           round_num=vote.round_num)
                deserialized_obj.add_vote(vote)
        return deserialized_obj

    def is_none(self) -> bool:
        if self._is_none is None:
            raise ValueError("Unknown votes status")
        return self._is_none


class EmptyVotes(ConsensusVotes):
    def __init__(self):
        super().__init__(b'', 0, 0)

    def add_vote(self, vote: 'ConsensusVote'):
        raise NotImplementedError

    def serialize(self, voters: Sequence[bytes]) -> List:
        raise NotImplementedError

    @classmethod
    def deserialize(cls: Type[T], votes: Sequence) -> T:
        raise NotImplementedError
