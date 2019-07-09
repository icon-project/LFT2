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
import pytest

from lft.consensus.factories import ConsensusData, ConsensusVotes
from lft.consensus.term import RotateTerm


class MockConsensusData(ConsensusData):
    @property
    def id(self) -> bytes:
        return

    @property
    def prev_id(self) -> bytes:
        return

    @property
    def leader(self) -> bytes:
        return self._leader

    @property
    def terms(self) -> int:
        return

    @property
    def height(self) -> int:
        return

    @property
    def round(self) -> int:
        return self._round

    @property
    def votes(self) -> ConsensusVotes:
        return

    def __init__(self, leader, round_):
        self._leader = leader
        self._round = round_


@pytest.mark.parametrize("round_num,rotate_term,leader_num", [(0, 1, 0), (10, 1, 0), (13, 1, 3),
                                                              (2, 3, 0), (29, 3, 9), (70, 5, 4)])
def test_rotate_term(round_num, rotate_term, leader_num):
    validators = [b'0', b'1', b'2', b'3', b'4', b'5', b'6', b'7', b'8', b'9']
    term = RotateTerm(0, rotate_term=rotate_term, validators=validators)
    consensus_data_mock = MockConsensusData(leader=validators[leader_num], round_=round_num)
    assert term.verify_data(consensus_data_mock)
