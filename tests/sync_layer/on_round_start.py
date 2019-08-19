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
from typing import Tuple

import pytest

from lft.app.data import DefaultConsensusData, DefaultConsensusDataFactory, DefaultConsensusVoteFactory
from lft.consensus.events import ProposeSequence, VoteSequence, BroadcastConsensusDataEvent, ReceivedConsensusDataEvent, \
    BroadcastConsensusVoteEvent, ReceivedConsensusVoteEvent, StartRoundEvent
from tests.sync_layer.on_sequence_vote_test import get_event
from tests.sync_layer.setup_sync_layer import setup_sync_layer, CANDIDATE_ID

QUORUM = 7


@pytest.mark.asyncio
async def test_on_round_start():
    """GIVEN a sync layer with init, and add complete that round
    WHEN run on_round_start
    THEN new round will be started and broadcast new data
    """
    # GIVEN
    event_system, sync_layer, voters, genesis_data = await setup_sync_layer(QUORUM)
    await sync_layer._on_sequence_propose(
        ProposeSequence(
            DefaultConsensusData(
                id_=b'data',
                prev_id=CANDIDATE_ID,
                proposer_id=voters[0],
                number=1,
                term_num=0,
                round_num=1,
                prev_votes=None
            )
        )
    )
    for voter in voters:
        vote = await DefaultConsensusVoteFactory(voter).create_vote(
            data_id=b'data',
            commit_id=CANDIDATE_ID,
            term_num=0,
            round_num=1
        )
        await sync_layer._on_sequence_vote(
            VoteSequence(vote)
        )

    # WHEN
    await sync_layer._on_start_round(
        StartRoundEvent(
            term_num=0,
            round_num=2,
            voters=voters
        )
    )

    # THEN
    event: BroadcastConsensusDataEvent = await get_event(event_system)
    isinstance(event, BroadcastConsensusDataEvent)
    assert event.data.prev_id == b'data'
    assert event.data.round_num == 2
    assert event.data.proposer_id == voters[1]
    assert event.data.term_num == 0
    assert event.data.number == 2
    prev_voters = []
    for prev_vote in event.data.prev_votes:
        assert prev_vote.term_num == 0
        assert prev_vote.data_id == b'data'
        assert prev_vote.round_num == 1
        assert prev_vote.commit_id == CANDIDATE_ID
        assert prev_vote.voter_id in voters
        prev_voters.append(prev_vote.voter_id)

    assert len(prev_voters) == len(voters)

    received_consensus_data_event = await get_event(event_system)
    isinstance(received_consensus_data_event, ReceivedConsensusDataEvent)
    assert received_consensus_data_event.data == event.data

    broadcast_vote_event: BroadcastConsensusVoteEvent = await get_event(event_system)
    isinstance(broadcast_vote_event, BroadcastConsensusVoteEvent)
    assert broadcast_vote_event.vote.voter_id == voters[1]
    assert broadcast_vote_event.vote.term_num == 0
    assert broadcast_vote_event.vote.round_num == 2
    assert broadcast_vote_event.vote.data_id == event.data.id
    assert broadcast_vote_event.vote.commit_id == b'data'

    received_vote_event: ReceivedConsensusVoteEvent = await get_event(event_system)
    isinstance(received_vote_event, ReceivedConsensusVoteEvent)
    assert broadcast_vote_event.vote == received_vote_event.vote
