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

from lft.app.data import DefaultVote, DefaultData
from lft.consensus.events import BroadcastVoteEvent, ReceivedVoteEvent
from tests.round_layer.setup_round_layer import setup_round_layer, CANDIDATE_ID, LEADER_ID, verify_no_events

PROPOSE_ID = b"b"


@pytest.mark.asyncio
@pytest.mark.parametrize("propose_id,propose_prev_id,expected_vote_data_id",
                         [(b"b", CANDIDATE_ID, b"b"),
                          (b"b", b"other_id", DefaultVote.NoneVote),
                          (LEADER_ID, None, DefaultVote.NoneVote)])
async def test_on_propose(propose_id, propose_prev_id, expected_vote_data_id):
    # TODO propose not data, correct data, non_connection_data
    """ GIVEN SyncLayer with candidate_data and ProposeSequence, setup
    WHEN raise ProposeSequence
    THEN Receive VoteEvent about ProposeSequence
    """
    # GIVEN
    event_system, round_layer, voters, genesis_data = await setup_round_layer(peer_num=7)
    event_system, round_layer, voters, genesis_data = await setup_round_layer(peer_num=7)
    propose = DefaultData(id_=PROPOSE_ID,
                          prev_id=propose_prev_id,
                          proposer_id=LEADER_ID,
                          number=1,
                          term_num=0,
                          round_num=0,
                          prev_votes=[])
    # WHEN
    await round_layer.propose_data(propose)
    # THEN

    non_deterministic, mono_ns, event = event_system.simulator._event_tasks.get_nowait()
    assert isinstance(event, BroadcastVoteEvent)
    assert event.vote.data_id == expected_vote_data_id

    non_deterministic, mono_ns, event = event_system.simulator._event_tasks.get_nowait()
    assert isinstance(event, ReceivedVoteEvent)
    assert event.vote.data_id == expected_vote_data_id

    # Test double propose
    # GIVEN
    second_propose = DefaultData(id_=PROPOSE_ID,
                                 prev_id=propose_prev_id,
                                 proposer_id=LEADER_ID,
                                 number=1,
                                 term_num=0,
                                 round_num=0,
                                 prev_votes=[])

    # WHEN
    await round_layer.propose_data(data=second_propose)
    # THEN
    await verify_no_events(event_system)
