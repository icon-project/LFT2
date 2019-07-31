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
from typing import Tuple, Sequence

from lft.consensus.events import InitializeEvent
from lft.consensus.layers.sync.sync_layer import SyncLayer
from lft.event import EventSystem
from tests.test_utils.test_datas import MockConsensusData
from tests.test_utils.test_factories import MockVoteFactory, MockDataFactory

CANDIDATE_ID = b'a'
SELF_ID = b'my_id'
BASIC_CANDIDATE_DATA = MockConsensusData(CANDIDATE_ID, None, b"leader", 0, 1, 0,
                                         None)


async def setup_sync_layer(quorum: int) -> Tuple[EventSystem, SyncLayer, Sequence[bytes]]:
    event_system = EventSystem(True)
    vote_factory = MockVoteFactory(SELF_ID)
    sync_layer = SyncLayer(event_system, MockDataFactory(), vote_factory)
    voters = [bytes([x]) for x in range(quorum)]

    init_event = InitializeEvent(
        term_num=0,
        round_num=1,
        candidate_data=BASIC_CANDIDATE_DATA,
        voters=voters
    )

    await sync_layer._on_init(init_event)

    return event_system, sync_layer, voters
