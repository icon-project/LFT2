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
import asyncio
from io import StringIO

import pytest

from lft.consensus.events import BroadcastConsensusVoteEvent, InitializeEvent, \
    ProposeSequence
from lft.consensus.factories import ConsensusVoteFactory, ConsensusVote, ConsensusVotes
from lft.consensus.layers.sync.sync_layer import SyncLayer
from lft.event import EventSystem
from lft.event.mediators import TimestampEventMediator, JsonRpcEventMediator
from tests.test_utils.test_datas import MockConsensusData, NONE_ID
from tests.test_utils.test_factories import MockVoteFactory, MockDataFactory


@pytest.mark.parametrize("candidate_id,propose_id,propose_prev_id,expected_vote_data_id",
                         [(b"a", b"b", b"a", b"b"),
                          (b"a", b"b", b"c", NONE_ID),
                          (b"a", NONE_ID, None, NONE_ID)])
def test_on_propose(candidate_id, propose_id, propose_prev_id, expected_vote_data_id):
    """ GIVEN SyncLayer with candidate_data and ProposeSequence, setup
    WHEN raise ProposeSequence
    THEN Receive VoteEvent about ProposeSequence
    """
    loop = asyncio.get_event_loop()

    async def async_on_propose():
        # GIVEN
        event_system, vote_factory, sync_layer = await _init_sync(candidate_id)

        propose = MockConsensusData(propose_id, propose_prev_id, vote_factory.voter_id,
                                    0, 2, 1, None)
        propose_event = ProposeSequence(propose)

        # WHEN
        await sync_layer._on_sequence_propose(propose_event)
        # THEN
        non_deterministic, mono_ns, event = event_system.simulator._event_tasks.get_nowait()
        assert isinstance(event, BroadcastConsensusVoteEvent)

        assert event.vote.data_id == expected_vote_data_id
    loop.run_until_complete(async_on_propose())


async def _init_sync(candidate_id):
    event_system = EventSystem(True)
    vote_factory = MockVoteFactory(b"my_id")
    candidate_data = MockConsensusData(candidate_id, None, b"leader", 0, 1, 0,
                                       None)
    print(f"prev_id: {candidate_id}")
    sync_layer = SyncLayer(event_system, MockDataFactory(), vote_factory)
    init_event = InitializeEvent(candidate_data=candidate_data, voters=[])
    await sync_layer._on_init(init_event)

    return event_system, vote_factory, sync_layer


def double_propose_test():
    # 위의 테스트를 함수로 쪼게서 실
    # callback_is_called, event_system, vote_factory = _init_sync(propose_prev_id)
    pass
