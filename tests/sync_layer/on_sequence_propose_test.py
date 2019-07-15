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

from lft.consensus.factories import ConsensusVoteFactory, ConsensusVote, ConsensusVotes
from lft.consensus.layers.sync.sync_layer import SyncLayer
from lft.event import EventSystem
from tests.test_utils.test_datas import MockConsensusData, NONE_ID
from tests.test_utils.test_factories import MockVoteFactory


@pytest.mark.parametrize("candidate_id,propose_id,propose_prev_id,expected_vote_id",
                         [(b"a", b"b", b"a", b"b"),
                          (b"a", b"b", b"c", NONE_ID),
                          (b"a", NONE_ID, None, NONE_ID)])
def propose_test(candidate_id, propose_id, propose_prev_id, expected_vote_id):
    """ GIVEN SyncLayer with candidate_data and ProposeSequence, setup
    WHEN raise ProposeSequence
    THEN Receive VoteEvent about ProposeSequence
    """
    # GIVEN
    callback_is_called, event_system, vote_factory = _init_sync(propose_prev_id)

    propose = MockConsensusData(propose_id, propose_prev_id, vote_factory.voter_id,
                                1, 2, 2, )

    propose_event = ReceiveProposeEvent(propose)

    # WHEN
    event_system.simulator.raise_event(propose_event)

    # THEN
    # run _vote_verify_handler
    assert callback_is_called


def _init_sync(propose_prev_id):
    event_system = EventSystem(True)
    vote_factory = MockVoteFactory(b"my_id")
    candidate_data = MockConsensusData(propose_prev_id, None, b"leader", 1, 1, 1,
                                       None)
    callback_is_called = False

    def _vote_verify_handler(vote_event: BroadcastVoteEvent):
        callback_is_called = True
        assert vote_event.vote.data_id == expected_vote_id

    event_system.simulator.register_handler(BroadcastVoteEvent, _vote_verify_handler)
    sycn_layer = SyncLayer(event_system, None, vote_factory, candidate_data)
    return callback_is_called, event_system, vote_factory


def double_propose_test():
    # 위의 테스트를 함수로 쪼게서 실
    callback_is_called, event_system, vote_factory = _init_sync(propose_prev_id)
