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

from lft.consensus.term import Term, RotateTerm


class TermFactory(ABC):
    @abstractmethod
    def create_term(self, term_num: int, voters: Sequence[bytes]) -> Term:
        raise NotImplementedError


class RotateTermFactory(TermFactory):
    def __init__(self, rotate_bound: int):
        self._rotate_bound = rotate_bound

    def create_term(self, term_num: int, voters: Sequence[bytes]) -> Term:
        return RotateTerm(num=term_num,
                          voters=voters,
                          rotate_bound=self._rotate_bound)
