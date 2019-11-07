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

from lft.app.data import DefaultData
from lft.app.term import RotateTerm
from lft.app.vote import DefaultVoteFactory
from lft.consensus.data import Data, Vote
from lft.consensus.events import BroadcastDataEvent, ReceivedDataEvent
from tests.round_layer.setup_round_layer import setup_round_layer, CANDIDATE_ID, get_event, verify_no_events

PEER_NUM = 7


@pytest.mark.asyncio
async def test_start_round():
    """GIVEN a sync layer with init, and add complete that round
    WHEN run on_round_start
    THEN new round will be started and broadcast new data
    """
    # GIVEN
    event_system, round_layer, voters, genesis_data = await setup_round_layer(PEER_NUM)
    await add_propose(event_system, round_layer, voters)

    await do_success_vote(round_layer, voters)

    # WHEN
    term = RotateTerm(0, voters)
    await round_layer.start_round(
        term=term,
        round_num=2
    )
    # pop done_round
    await get_event(event_system)

    # THEN
    consensus_data = await verify_data_events(
        event_system=event_system,
        prev_id=b'data',
        round_num=2,
        proposer_id=voters[2],
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
    await verify_no_events(event_system)

    return round_layer, event_system, voters


@pytest.mark.asyncio
async def test_prev_round_is_failed():
    # GIVEN
    event_system, round_layer, voters, genesis_data = await setup_round_layer(PEER_NUM)
    await add_propose(event_system, round_layer, voters)

    for voter in voters:
        vote = await DefaultVoteFactory(voter).create_none_vote(
            term_num=0,
            round_num=1
        )
        await round_layer.vote_data(vote)

    # WHEN
    term = RotateTerm(0, voters)
    await round_layer.start_round(
        term=term,
        round_num=2
    )
    event = await get_event(event_system)

    # THEN
    consensus_data = await verify_data_events(
        event_system=event_system,
        prev_id=CANDIDATE_ID,
        round_num=2,
        proposer_id=voters[2],
        term_num=0,
        number=1
    )

    await verify_no_events(event_system)


async def do_success_vote(round_layer, voters):
    for voter in voters:
        vote = await DefaultVoteFactory(voter).create_vote(
            data_id=b'data',
            commit_id=CANDIDATE_ID,
            term_num=0,
            round_num=1
        )
        await round_layer.vote_data(vote)


async def add_propose(event_system, round_layer, voters):
    await round_layer.propose_data(
        DefaultData(
            id_=b'data',
            prev_id=CANDIDATE_ID,
            proposer_id=voters[1],
            number=1,
            term_num=0,
            round_num=1,
            prev_votes=[]
        )
    )
    # pop vote
    event = await get_event(event_system)
    event = await get_event(event_system)


async def verify_data_events(event_system, prev_id, round_num, proposer_id, term_num, number) -> Data:
    broadcast_data_event: BroadcastDataEvent = await get_event(event_system)
    assert isinstance(broadcast_data_event, BroadcastDataEvent)
    assert broadcast_data_event.data.prev_id == prev_id
    assert broadcast_data_event.data.round_num == round_num
    assert broadcast_data_event.data.proposer_id == proposer_id
    assert broadcast_data_event.data.term_num == term_num
    assert broadcast_data_event.data.number == number

    received_data_event: ReceivedDataEvent = await get_event(event_system)
    assert isinstance(received_data_event, ReceivedDataEvent)
    assert received_data_event.data == broadcast_data_event.data

    return received_data_event.data


def verify_prev_votes(consensus_data: Data, prev_id, round_num, term_num, commit_id, voters):
    compare_voters = []
    for vote in consensus_data.prev_votes:
        if isinstance(vote, Vote):
            assert vote.term_num == term_num
            assert vote.round_num == round_num
            assert vote.commit_id == commit_id
            assert vote.data_id == prev_id
            assert vote.data_id == consensus_data.prev_id
            assert vote.voter_id in voters
            compare_voters.append(vote.voter_id)
    assert len(compare_voters) >= (2 * len(voters)) / 3
