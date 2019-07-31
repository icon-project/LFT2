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

from lft.consensus.events import DoneRoundEvent
from tests.sync_layer.setup_sync_layer import BASIC_CANDIDATE_DATA, setup_sync_layer
from tests.test_utils.test_datas import MockConsensusData, MockVote
from tests.test_utils.test_factories import MockVoteFactory

QUORUM = 7
LEADER_ID = bytes([0])
PROPOSE_ID = b'propose'

now_data = MockConsensusData(id_=PROPOSE_ID,
                             prev_id=BASIC_CANDIDATE_DATA.id,
                             proposer=LEADER_ID,
                             term_num=0,
                             number=1,
                             round_num=1,
                             votes=[])



@pytest.mark.parametrize("success_vote_num, none_vote_num, not_vote_num, is_success, is_complete",
                         [(5, 2, 0, True, True),
                          (5, 0, 0, True, True),
                          (2, 5, 0, False, True),
                          (0, 5, 0, False, True),
                          (3, 4, 0, False, True),
                          (4, 0, 0, False, False),
                          (4, 0, 3, False, True)]
                         )
def test_on_vote_sequence(success_vote_num, none_vote_num, not_vote_num, is_success, is_complete):
    """ GIVEN SyncRound and propose data,
    WHEN repeats _on_add_votes amount of vote_num
    THEN raised expected DoneRoundEvent
    """
    async def testcase():
        mock_vote_factory = MockVoteFactory()
        event_system, sync_layer, voters = await setup_sync_layer(QUORUM)
        for i in range(success_vote_num):
            sync_layer._on_sequence_vote(MockVote())

