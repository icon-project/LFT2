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
from abc import ABC, abstractmethod
from typing import Sequence

from lft.consensus.data import ConsensusData, ConsensusVote


class Term(ABC):
    @property
    @abstractmethod
    def num(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def quorum_num(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def verify_data(self, data: ConsensusData):
        raise NotImplementedError

    @abstractmethod
    def verify_vote(self, vote: ConsensusVote, vote_index: int = -1):
        raise NotImplementedError

    @abstractmethod
    def verify_proposer(self, proposer_id: bytes, round_num: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_proposer_id(self, round_num: int) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def get_voter_id(self, vote_index: int) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def get_voters_id(self) -> Sequence[bytes]:
        raise NotImplementedError


class InvalidProposer(Exception):
    def __init__(self, proposer: bytes, expected: bytes):
        self.proposer = proposer
        self.expected = expected


class InvalidVoter(Exception):
    def __init__(self, voter: bytes, expected: bytes):
        self.voter = voter
        self.expected = expected
