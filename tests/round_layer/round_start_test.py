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
from lft.consensus.events import BroadcastDataEvent, ReceiveDataEvent
from tests.round_layer.setup_round_layer import setup_round_layer, CANDIDATE_ID

PEER_NUM = 7


@pytest.mark.asyncio
async def test_round_start():
    # GIVEN
    event_system, round_layer, voters = await setup_round_layer(PEER_NUM)

    # WHEN
    round_layer._round_num = voters.index(round_layer._node_id)
    await round_layer.round_start()

    # THEN
    broadcast_data_event = event_system.simulator.raise_event.call_args_list[0][0][0]
    assert isinstance(broadcast_data_event, BroadcastDataEvent)
    assert broadcast_data_event.data.prev_id == CANDIDATE_ID
    assert broadcast_data_event.data.round_num == round_layer._round_num
    assert broadcast_data_event.data.proposer_id == round_layer._node_id
    assert broadcast_data_event.data.term_num == round_layer._term.num
    assert broadcast_data_event.data.number == 1

    receive_data_event = event_system.simulator.raise_event.call_args_list[1][0][0]
    assert isinstance(receive_data_event, ReceiveDataEvent)
    assert receive_data_event.data == broadcast_data_event.data
