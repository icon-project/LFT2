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
from typing import Tuple, Sequence, List

import pytest

from lft.app.data import DefaultConsensusVoteFactory, DefaultConsensusDataFactory, DefaultConsensusData
from lft.consensus.data import ConsensusData
from lft.consensus.events import InitializeEvent
from lft.consensus.layers.sync.sync_layer import SyncLayer
from lft.consensus.term.factories import RotateTermFactory
from lft.event import EventSystem

CANDIDATE_ID = b'a'
TEST_NODE_ID = bytes([2])
LEADER_ID = bytes([1])


async def setup_sync_layer(peer_num: int) -> Tuple[EventSystem, SyncLayer, List[bytes], ConsensusData]:

    event_system = EventSystem(True)
    voters = [bytes([x]) for x in range(peer_num)]
    vote_factory = DefaultConsensusVoteFactory(TEST_NODE_ID)
    data_factory = DefaultConsensusDataFactory(TEST_NODE_ID)
    term_factory = RotateTermFactory(1)
    genesis_data = DefaultConsensusData(
        id_=CANDIDATE_ID,
        prev_id=None,
        proposer_id=TEST_NODE_ID,
        number=0,
        term_num=0,
        round_num=0,
        prev_votes=None
    )

    sync_layer = SyncLayer(event_system, data_factory, vote_factory, term_factory)

    init_event = InitializeEvent(
        term_num=0,
        round_num=1,
        node_id=TEST_NODE_ID,
        candidate_data=genesis_data,
        voters=voters,
        votes=None
    )
    await sync_layer._on_event_initialize(init_event)

    return event_system, sync_layer, voters, genesis_data


async def get_event(event_system):
    non_deterministic, mono_ns, event = event_system.simulator._event_tasks.get_nowait()
    return event


async def verify_no_events(event_system):
    with pytest.raises(QueueEmpty):
        event = await get_event(event_system)
        print("remain event: " + event)
