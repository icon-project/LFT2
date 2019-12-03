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

from lft.app.data import DefaultData
from lft.app.vote import DefaultVoteFactory
from lft.consensus.events import RoundEndEvent
from tests.round_layer.setup_round_layer import setup_round_layer, CANDIDATE_ID, LEADER_ID

PEER_NUM = 7
PROPOSE_ID = b'propose'


@pytest.mark.asyncio
@pytest.mark.parametrize("success_vote_num, none_vote_num, lazy_vote_num, expected_success, expected_complete",
                         [(5, 2, 0, True, True),
                          (5, 0, 0, True, True),
                          (2, 5, 0, False, True),
                          (0, 5, 0, False, True),
                          (3, 4, 0, False, True),
                          (4, 0, 0, False, False),
                          (4, 1, 2, False, True)]
                         )
async def test_on_vote_sequence(success_vote_num, none_vote_num, lazy_vote_num, expected_success, expected_complete):
    """ GIVEN SyncRound and propose data,
    WHEN repeats _on_add_votes amount of vote_num
    THEN raised expected RoundEndEvent
    """

    # GIVEN
    event_system, round_layer, voters = await setup_round_layer(PEER_NUM)
    await round_layer.round_start()

    consensus_data = DefaultData(
        id_=PROPOSE_ID,
        prev_id=CANDIDATE_ID,
        proposer_id=LEADER_ID,
        number=1,
        term_num=0,
        round_num=1,
        prev_votes=[]
    )

    await round_layer.receive_data(data=consensus_data)
    event_system.simulator.raise_event.reset_mock()

    # WHEN
    async def do_vote(vote):
        await round_layer.receive_vote(vote)

    validator_vote_factories = [DefaultVoteFactory(x) for x in voters]
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

    for i in range(lazy_vote_num):
        await do_vote(
            await validator_vote_factories[success_vote_num + none_vote_num + i].create_lazy_vote(
                voter_id=voters[success_vote_num + none_vote_num + i],
                term_num=0,
                round_num=1
            )
        )

    # THEN
    if expected_complete:
        event_system.simulator.raise_event.called_once()
        event = event_system.simulator.raise_event.call_args_list[0][0][0]
        assert isinstance(event, RoundEndEvent)
        if expected_success:
            verify_success_round_end(round_end=event,
                                     expected_candidate_id=consensus_data.id,
                                     expected_commit_id=CANDIDATE_ID)

        else:
            verify_fail_round_end(round_end=event)


def verify_fail_round_end(round_end: RoundEndEvent):
    verify_round_num_is_correct(round_end)
    assert not round_end.candidate_id
    assert not round_end.commit_id


def verify_success_round_end(round_end: RoundEndEvent,
                             expected_candidate_id: bytes,
                             expected_commit_id: bytes):
    assert round_end.candidate_id
    verify_round_num_is_correct(round_end)
    assert round_end.candidate_id == expected_candidate_id
    assert round_end.commit_id == expected_commit_id


def verify_round_num_is_correct(round_end):
    assert round_end.round_num == 1
    assert round_end.term_num == 0
