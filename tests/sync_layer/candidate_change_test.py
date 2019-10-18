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

from lft.app.data import DefaultData, DefaultVoteFactory
from lft.consensus.events import ProposeSequence, VoteSequence, DoneRoundEvent, StartRoundEvent, \
    BroadcastVoteEvent
from tests.sync_layer.setup_sync_layer import *


@pytest.mark.asyncio
async def test_candidate_change_by_vote():
    """ GIVEN SyncRound and setup candidate data
    WHEN Propose new data that has same number with candidate data
    THEN SyncRound raises done_round with changed_candidate_data
    """
    # GIVEN
    event_system, sync_layer, voters, genesis_data = await setup_sync_layer(peer_num=7)
    first_candidate_id = await add_first_candidate(event_system, sync_layer, voters)
    for voter in voters:
        await sync_layer._on_sequence_vote(
            VoteSequence(
                await DefaultVoteFactory(voter).create_vote(
                    data_id=first_candidate_id,
                    commit_id=CANDIDATE_ID,
                    term_num=0,
                    round_num=1
                )
            )
        )
    # pop done_round_event
    await get_event(event_system)
    # WHEN
    await sync_layer._on_event_start_round(
        StartRoundEvent(
            term_num=0,
            round_num=2,
            voters=voters
        )
    )
    await get_event(event_system)
    await get_event(event_system)

    second_candidate_id = b'second_candidate'
    second_candidate_data = DefaultData(
        id_=second_candidate_id,
        prev_id=CANDIDATE_ID,
        proposer_id=voters[2],
        number=1,
        term_num=0,
        round_num=2,
        prev_votes=[]
    )
    await sync_layer._on_sequence_propose(
        ProposeSequence(second_candidate_data)
    )
    event: BroadcastVoteEvent = await get_event(event_system)

    # Pop received event
    await get_event(event_system)

    await verify_no_events(event_system)

    for voter in voters:
         await sync_layer._on_sequence_vote(
             VoteSequence(
                await DefaultVoteFactory(voter).create_vote(
                    data_id=second_candidate_id,
                    commit_id=CANDIDATE_ID,
                    term_num=0,
                    round_num=2
                )
             )
         )

    # THEN
    event: DoneRoundEvent = await get_event(event_system)
    assert isinstance(event, DoneRoundEvent)
    assert event.candidate_data == second_candidate_data
    assert event.commit_id == genesis_data.id
    assert event.round_num == 2
    assert event.term_num == 0


async def add_first_candidate(event_system, sync_layer, voters):
    first_candidate_id = b'first_candidate'
    await sync_layer._on_sequence_propose(
        ProposeSequence(
            DefaultData(
                id_=first_candidate_id,
                prev_id=CANDIDATE_ID,
                proposer_id=voters[1],
                number=1,
                term_num=0,
                round_num=1,
                prev_votes=[]
            )
        )
    )
    # pop vote event
    await get_event(event_system)
    await get_event(event_system)
    return first_candidate_id


@pytest.mark.asyncio
async def test_candidate_change_by_data():
    """ GIVEN sync_layer that has failed candidate data
    WHEN add new propose with success votes for prev round
    THEN sync_layer change candidate data to that data
    """
    # GIVEN
    event_system, sync_layer, voters, genesis_data = await setup_sync_layer(peer_num=7)
    first_candidate_id = await add_first_candidate(event_system, sync_layer, voters)

    for voter in voters[:2]:
        await sync_layer._on_sequence_vote(
            VoteSequence(
                await DefaultVoteFactory(voter).create_vote(
                    data_id=first_candidate_id,
                    commit_id=CANDIDATE_ID,
                    term_num=0,
                    round_num=1
                )
            )
        )
    for voter in voters[2:]:
        await sync_layer._on_sequence_vote(
            VoteSequence(
                await DefaultVoteFactory(voter).create_not_vote(
                    voter_id=voter,
                    term_num=0,
                    round_num=1
                )
            )
        )
    await get_event(event_system)
    # WHEN

    await sync_layer._on_event_start_round(
        StartRoundEvent(
            term_num=0,
            round_num=2,
            voters=voters
        )
    )
    await get_event(event_system)
    await get_event(event_system)

    success_votes = [await DefaultVoteFactory(voter).create_vote(first_candidate_id, CANDIDATE_ID, 0, 1)
                     for voter in voters]

    second_data_id = b'second_data'
    await sync_layer._on_sequence_propose(
        ProposeSequence(
            DefaultData(
                id_=second_data_id,
                prev_id=first_candidate_id,
                proposer_id=voters[2],
                number=2,
                term_num=0,
                round_num=2,
                prev_votes=success_votes
            )
        )
    )

    # THEN
    event: BroadcastVoteEvent = await get_event(event_system)
    assert isinstance(event, BroadcastVoteEvent)
    assert event.vote.data_id == second_data_id
    assert event.vote.commit_id == first_candidate_id

    event: BroadcastVoteEvent = await get_event(event_system)
    await verify_no_events(event_system)
