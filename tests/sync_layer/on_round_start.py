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
from asyncio import QueueEmpty
from typing import Tuple

import pytest

from lft.app.data import DefaultConsensusData, DefaultConsensusDataFactory, DefaultConsensusVoteFactory
from lft.consensus.data import ConsensusData
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
    # pop vote
    event = await get_event(event_system)
    event = await get_event(event_system)

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
    # pop done_round
    event = await get_event(event_system)

    # THEN
    consensus_data = await verify_data_events(
        event_system=event_system,
        prev_id=b'data',
        round_num=2,
        proposer_id=voters[1],
        term_num=0,
        number=2
    )
    verify_prev_votes(
        consensus_data=consensus_data,
        prev_id=b'data',
        round_num=1,
        term_num=0,
        commit_id=CANDIDATE_ID,
        voters=voters
    )
    await verify_vote_events(
        event_system=event_system,
        data_id=consensus_data.id,
        commit_id=b'data',
        round_num=2,
        term_num=0
    )

    with pytest.raises(QueueEmpty):
        event = await get_event(event_system)
        print("remain event: " + event)


async def verify_data_events(event_system, prev_id, round_num, proposer_id, term_num, number) -> ConsensusData:
    broadcast_data_event: BroadcastConsensusDataEvent = await get_event(event_system)
    assert isinstance(broadcast_data_event, BroadcastConsensusDataEvent)
    assert broadcast_data_event.data.prev_id == prev_id
    assert broadcast_data_event.data.round_num == round_num
    assert broadcast_data_event.data.proposer_id == proposer_id
    assert broadcast_data_event.data.term_num == term_num
    assert broadcast_data_event.data.number == number

    received_data_event: ReceivedConsensusDataEvent = await get_event(event_system)
    assert isinstance(received_data_event, ReceivedConsensusDataEvent)
    assert received_data_event.data == broadcast_data_event.data

    return received_data_event.data


def verify_prev_votes(consensus_data: ConsensusData, prev_id, round_num, term_num, commit_id, voters):
    compare_voters = []
    for vote in consensus_data.prev_votes:
        assert vote.term_num == term_num
        assert vote.round_num == round_num
        assert vote.commit_id == commit_id
        assert vote.data_id == prev_id
        assert vote.data_id == consensus_data.prev_id
        assert vote.voter_id in voters
        compare_voters.append(vote.voter_id)
    assert len(compare_voters) == len(voters)


async def verify_vote_events(event_system, data_id, commit_id, round_num, term_num):
    broadcast_vote_event: BroadcastConsensusVoteEvent = await get_event(event_system)
    assert isinstance(broadcast_vote_event, BroadcastConsensusVoteEvent)

    assert broadcast_vote_event.vote.data_id == data_id
    assert broadcast_vote_event.vote.commit_id == commit_id
    assert broadcast_vote_event.vote.term_num == term_num
    assert broadcast_vote_event.vote.round_num == round_num

    received_vote_event: ReceivedConsensusVoteEvent = await get_event(event_system)
    assert isinstance(received_vote_event, ReceivedConsensusVoteEvent)
    assert received_vote_event.vote == broadcast_vote_event.vote
