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
from unittest.mock import MagicMock
from typing import Tuple, List
from lft.app.data import DefaultDataFactory, DefaultData
from lft.app.vote import DefaultVoteFactory
from lft.app.epoch import RotateEpoch
from lft.consensus.messages.data import DataPool
from lft.consensus.messages.vote import VotePool
from lft.consensus.layers.round import RoundLayer
from lft.event import EventSystem

CANDIDATE_ID = b'a'
TEST_NODE_ID = bytes([2])
LEADER_ID = bytes([1])


async def setup_round_layer(peer_num: int) -> Tuple[EventSystem, RoundLayer, List[bytes]]:
    event_system = MagicMock(EventSystem())
    voters = [bytes([x]) for x in range(peer_num)]
    data_factory = DefaultDataFactory(TEST_NODE_ID)
    vote_factory = DefaultVoteFactory(TEST_NODE_ID)
    data_pool = DataPool()
    vote_pool = VotePool()

    genesis_data = DefaultData(
        id_=CANDIDATE_ID,
        prev_id=b'',
        proposer_id=TEST_NODE_ID,
        number=0,
        epoch_num=0,
        round_num=0,
        prev_votes=()
    )
    data_pool.add_data(genesis_data)

    round_layer = RoundLayer(TEST_NODE_ID, RotateEpoch(0, voters), genesis_data.round_num + 1,
                             event_system, data_factory, vote_factory, data_pool, vote_pool)
    round_layer._candidate_id = CANDIDATE_ID
    return event_system, round_layer, voters
