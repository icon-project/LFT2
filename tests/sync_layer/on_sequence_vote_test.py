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

from lft.app.data import DefaultConsensusData, DefaultConsensusVoteFactory
from lft.consensus.data import ConsensusData
from lft.consensus.events import DoneRoundEvent, ProposeSequence, VoteSequence, BroadcastConsensusVoteEvent, \
    ReceivedConsensusVoteEvent
from tests.sync_layer.setup_sync_layer import setup_sync_layer, CANDIDATE_ID, LEADER_ID, get_event, verify_no_events

PEER_NUM = 7
PROPOSE_ID = b'propose'


@pytest.mark.asyncio
@pytest.mark.parametrize("success_vote_num, none_vote_num, not_vote_num, expected_success, expected_complete",
                         [(5, 2, 0, True, True),
                          (5, 0, 0, True, True),
                          (2, 5, 0, False, True),
                          (0, 5, 0, False, True),
                          (3, 4, 0, False, True),
                          (4, 0, 0, False, False),
                          (4, 1, 2, False, True)]
                         )
async def test_on_vote_sequence(success_vote_num, none_vote_num, not_vote_num, expected_success, expected_complete):
    """ GIVEN SyncRound and propose data,
    WHEN repeats _on_add_votes amount of vote_num
    THEN raised expected DoneRoundEvent
    """

    # GIVEN
    event_system, sync_layer, voters, genesis_data = await setup_sync_layer(PEER_NUM)

    consensus_data = DefaultConsensusData(
        id_=PROPOSE_ID,
        prev_id=CANDIDATE_ID,
        proposer_id=LEADER_ID,
        number=1,
        term_num=0,
        round_num=1,
        prev_votes=None
    )

    await sync_layer._on_sequence_propose(
        ProposeSequence(
            data=consensus_data
        )
    )
    validator_vote_factories = [DefaultConsensusVoteFactory(x) for x in voters]

    # pop unnecessary event
    my_vote: BroadcastConsensusVoteEvent = await get_event(event_system)
    my_vote: ReceivedConsensusVoteEvent = await get_event(event_system)

    # WHEN
    async def do_vote(vote):
        await sync_layer._on_sequence_vote(
            VoteSequence(vote)
        )

    for i in range(success_vote_num):
        await do_vote(
            await validator_vote_factories[i].create_vote(
                data_id=PROPOSE_ID,
                commit_id=CANDIDATE_ID,
                term_num=0,
                round_num=1
            )
        )
    for i in range(none_vote_num):
        await do_vote(
            await validator_vote_factories[success_vote_num + i].create_none_vote(
                term_num=0,
                round_num=1
            )
        )

    for i in range(not_vote_num):
        await do_vote(
            await validator_vote_factories[success_vote_num + none_vote_num + i].create_not_vote(
                voter_id=voters[success_vote_num + none_vote_num + i],
                term_num=0,
                round_num=1
            )
        )

    # THEN
    if expected_complete:
        done_round: DoneRoundEvent = await get_event(event_system)
        if expected_success:
            verify_success_done_round(done_round=done_round,
                                      expected_candidate=consensus_data,
                                      expected_commit=genesis_data)

        else:
            verify_fail_done_round(done_round=done_round)

    await verify_no_events(event_system)


def verify_fail_done_round(done_round: DoneRoundEvent):
    assert not done_round.is_success
    verify_round_num_is_correct(done_round)
    assert not done_round.candidate_data
    assert not done_round.commit_id


def verify_success_done_round(done_round: DoneRoundEvent,
                              expected_candidate: ConsensusData,
                              expected_commit: ConsensusData):
    assert done_round.is_success
    verify_round_num_is_correct(done_round)
    assert done_round.candidate_data == expected_candidate
    assert done_round.commit_id == expected_commit.id


def verify_round_num_is_correct(done_round):
    assert done_round.round_num == 1
    assert done_round.term_num == 0
