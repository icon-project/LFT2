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
from typing import List

from lft.consensus.factories import ConsensusData
from lft.consensus.term import Term


class RotateTerm(Term):
    def __init__(self, num: int, validators: List[bytes], rotate_term: int = 1):
        self._num = num
        self._rotate_term = rotate_term
        self.validators = validators

    @property
    def num(self) -> int:
        return self._num

    def verify_data(self, data: ConsensusData) -> bool:
        return data.proposer == self.get_proposer(data.round_num)

    def verify_proposer(self, proposer: bytes, round_num: int) -> bool:
        return proposer == self.get_proposer(round_num)

    def get_proposer(self, round_num: int) -> bytes:
        return self.validators[int(round_num / self._rotate_term) % len(self.validators)]
