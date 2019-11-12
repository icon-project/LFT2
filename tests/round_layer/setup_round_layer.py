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
from asyncio.queues import QueueEmpty
from typing import Tuple, List

import pytest

from lft.app.data import DefaultDataFactory, DefaultData
from lft.app.vote import DefaultVoteFactory
from lft.app.term import RotateTerm
from lft.consensus.messages.data import Data
from lft.consensus.layers.round_layer import RoundLayer
from lft.event import EventSystem

CANDIDATE_ID = b'a'
TEST_NODE_ID = bytes([2])
LEADER_ID = bytes([1])


async def setup_round_layer(peer_num: int) -> Tuple[EventSystem, RoundLayer, List[bytes], Data]:
    event_system = EventSystem()
    voters = [bytes([x]) for x in range(peer_num)]
    vote_factory = DefaultVoteFactory(TEST_NODE_ID)
    data_factory = DefaultDataFactory(TEST_NODE_ID)
    genesis_data = DefaultData(
        id_=CANDIDATE_ID,
        prev_id=b'',
        proposer_id=TEST_NODE_ID,
        number=0,
        term_num=0,
        round_num=0,
        prev_votes=[]
    )

    round_layer = RoundLayer(TEST_NODE_ID, event_system, data_factory, vote_factory)
    await round_layer.initialize(term=RotateTerm(0, voters), round_num=1, candidate_data=genesis_data, votes=[])

    return event_system, round_layer, voters, genesis_data


async def get_event(event_system):
    non_deterministic, mono_ns, event = event_system.simulator._event_tasks.get_nowait()
    return event


async def verify_no_events(event_system):
    with pytest.raises(QueueEmpty):
        event = await get_event(event_system)
        print("remain event: " + event)
