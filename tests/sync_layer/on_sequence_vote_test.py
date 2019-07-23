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
from tests.sync_layer.setup_sync_layer import BASIC_CANDIDATE_DATA
from tests.test_utils.test_datas import MockConsensusData
now_data = MockConsensusData(propose_id, propose_prev_id, vote_factory.voter_id,
                                    0, 2, 1, None)

# TODO need vote
success_end = DoneRoundEvent(term_num=0,
                             round_num=1,
                             is_success=True,
                             candidate_data=now_data,
                             commit_data=BASIC_CANDIDATE_DATA)

fail_end = DoneRoundEvent(term_num=0,
                          round_num=1,
                          is_success=False)


@pytest.mark.parametrize("round_end", [(success_end), (fail_end)])
def test_on_vote_sequence(round_end):
    print(round_end)

