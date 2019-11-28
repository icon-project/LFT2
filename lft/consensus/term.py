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
from abc import abstractmethod
from typing import Sequence, Dict

from lft.consensus.messages.data import Data, Vote
from lft.serialization import Serializable


class Term(Serializable):
    @property
    @abstractmethod
    def num(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def quorum_num(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def voters_num(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def voters(self) -> Sequence[bytes]:
        raise NotImplementedError

    @abstractmethod
    def verify_data(self, data: Data):
        raise NotImplementedError

    @abstractmethod
    def verify_vote(self, vote: Vote, vote_index: int = -1):
        raise NotImplementedError

    @abstractmethod
    def verify_proposer(self, proposer_id: bytes, round_num: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def verify_voter(self, voter: bytes, vote_index: int = -1):
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

    @abstractmethod
    def __eq__(self, other):
        raise NotImplementedError


class TermPool:
    def __init__(self):
        self._terms: Dict[int, Term] = {}

    def add_term(self, term: Term):
        self._terms[term.num] = term

    def get_term(self, term_num: int):
        return self._terms[term_num]

    def trim_term(self, latest_term_num: int):
        self._terms = {term_num: term for term_num, term in self._terms.items()
                       if term.num >= latest_term_num}
