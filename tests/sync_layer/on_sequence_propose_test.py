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
from asyncio import QueueEmpty

import pytest

from lft.consensus.default_data.data import DefaultConsensusVote, DefaultConsensusData
from lft.consensus.events import BroadcastConsensusVoteEvent, ProposeSequence
from tests.sync_layer.setup_sync_layer import setup_sync_layer, CANDIDATE_ID, LEADER_ID


PROPOSE_ID = b"b"
@pytest.mark.parametrize("propose_id,propose_prev_id,expected_vote_data_id",
                         [(b"b", CANDIDATE_ID, b"b"),
                          (b"b", b"other_id", DefaultConsensusVote.NoneVote),
                          (LEADER_ID, None, DefaultConsensusVote.NoneVote)])
def test_on_propose(propose_id, propose_prev_id, expected_vote_data_id):
    # TODO propose not data, correct data, non_connection_data
    """ GIVEN SyncLayer with candidate_data and ProposeSequence, setup
    WHEN raise ProposeSequence
    THEN Receive VoteEvent about ProposeSequence
    """
    async def async_on_propose():
        # GIVEN
        event_system, sync_layer, voters, data_factory, vote_factory = await setup_sync_layer(quorum=7)
        propose = DefaultConsensusData(id_=PROPOSE_ID,
                                       prev_id=propose_prev_id,
                                       proposer_id=LEADER_ID,
                                       number=1,
                                       term_num=0,
                                       round_num=0,
                                       prev_votes=None)
        propose_event = ProposeSequence(propose)

        # WHEN
        await sync_layer._on_sequence_propose(propose_event)
        # THEN
        non_deterministic, mono_ns, event = event_system.simulator._event_tasks.get_nowait()
        assert isinstance(event, BroadcastConsensusVoteEvent)
        assert event.vote.data_id == expected_vote_data_id

        # Test double propose
        # GIVEN
        second_propose = DefaultConsensusData(id_=PROPOSE_ID,
                                              prev_id=propose_prev_id,
                                              proposer_id=LEADER_ID,
                                              number=1,
                                              term_num=0,
                                              round_num=0,
                                              prev_votes=None)

        # WHEN
        await sync_layer._on_sequence_propose(ProposeSequence(data=second_propose))
        with pytest.raises(QueueEmpty):
            event_system.simulator._event_tasks.get_nowait()
        print("Success")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_on_propose())
