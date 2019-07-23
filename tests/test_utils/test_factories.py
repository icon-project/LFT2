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
from lft.consensus.factories import ConsensusVoteFactory, ConsensusVote, ConsensusDataFactory, \
    ConsensusDataVerifier, ConsensusData
from tests.test_utils.test_datas import MockVote, NONE_ID


class MockVoteFactory(ConsensusVoteFactory):

    async def create_not_vote(self, voter_id: bytes) -> 'ConsensusVote':
        pass

    async def create_vote_verifier(self) -> 'ConsensusVoteVerifier':
        pass

    def __init__(self, voter_id: bytes):
        self.voter_id = voter_id

    async def create_vote(self, data_id: bytes, term_num: int, round_num: int) -> 'ConsensusVote':
        return MockVote(self._create_id(data_id, term_num, round_num),
                        data_id, term_num, self.voter_id, round_num)

    async def create_none_vote(self, term_num: int, round_num: int) -> 'ConsensusVote':
        return MockVote(self._create_id(NONE_ID, term_num, round_num),
                        NONE_ID, term_num, self.voter_id, round_num)

    def _create_id(self, data_id: bytes, term_num: int, round_num: int) -> bytes:
        return self.voter_id + data_id + bytes([term_num]) + bytes([round_num])


class MockDataFactory(ConsensusDataFactory):
    async def create_not_data(self, number: int, term_num: int, round_num: int) -> 'ConsensusData':
        pass

    async def create_data(self) -> 'ConsensusData':
        pass

    async def create_data_verifier(self, data: 'ConsensusData') -> 'ConsensusDataVerifier':
        return MockConsensusDataVerifier()


class MockConsensusDataVerifier(ConsensusDataVerifier):

    async def verify(self):
        # Always success
        pass
