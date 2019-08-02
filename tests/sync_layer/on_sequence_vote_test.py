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

from lft.consensus.default_data.data import DefaultConsensusData, DefaultConsensusVote
from lft.consensus.default_data.factories import DefaultConsensusVoteFactory
from lft.consensus.events import DoneRoundEvent, ProposeSequence, VoteSequence, BroadcastConsensusVoteEvent
from lft.consensus.factories import ConsensusVoteFactory
from tests.sync_layer.setup_sync_layer import setup_sync_layer, CANDIDATE_ID, LEADER_ID, SELF_ID

QUORUM = 7
PROPOSE_ID = b'propose'


class VoteEvent(object):
    pass


@pytest.mark.parametrize("success_vote_num, none_vote_num, not_vote_num, is_success, is_complete",
                         [(5, 2, 0, True, True),
                          (5, 0, 0, True, True),
                          (2, 5, 0, False, True),
                          (0, 5, 0, False, True),
                          (3, 4, 0, False, True),
                          (4, 0, 0, False, False),
                          (4, 1, 2, False, True)]
                         )
def test_on_vote_sequence(success_vote_num, none_vote_num, not_vote_num, is_success, is_complete):
    """ GIVEN SyncRound and propose data,
    WHEN repeats _on_add_votes amount of vote_num
    THEN raised expected DoneRoundEvent
    """
    async def testcase():
        event_system, sync_layer, voters = await setup_sync_layer(QUORUM)
        success_propose_is_come = success_vote_num != 0
        if success_propose_is_come:
            await sync_layer._on_sequence_propose(
                ProposeSequence(
                    DefaultConsensusData(
                        id_=PROPOSE_ID,
                        prev_id=CANDIDATE_ID,
                        proposer_id=LEADER_ID,
                        number=1,
                        term_num=0,
                        round_num=1,
                        prev_votes=None
                    )
                )
            )
        else:
            await sync_layer._on_sequence_propose(
                ProposeSequence(
                    DefaultConsensusData(
                        id_=LEADER_ID,
                        prev_id=LEADER_ID,
                        proposer_id=LEADER_ID,
                        number=1,
                        term_num=0,
                        round_num=1,
                        prev_votes=None
                    )
                )
            )
        # Remove LEADER and SELF
        voters.remove(LEADER_ID)
        voters.remove(SELF_ID)
        validator_vote_factories = [DefaultConsensusVoteFactory(x) for x in voters]

        async def do_success_vote(vote_factory: ConsensusVoteFactory):
            await sync_layer._on_sequence_vote(
                VoteSequence(
                    vote=await vote_factory.create_vote(
                        data_id=PROPOSE_ID,
                        term_num=0,
                        round_num=1
                    )
                )
            )

        async def do_none_vote(vote_factory: ConsensusVoteFactory):
            await sync_layer._on_sequence_vote(
                VoteSequence(
                    vote=await vote_factory.create_none_vote(
                        term_num=0,
                        round_num=1
                    )
                )
            )

        async def do_not_vote(voter_id: bytes):
            await sync_layer._on_sequence_vote(
                VoteSequence(
                    vote=await validator_vote_factories[0].create_not_vote(
                        voter_id=voter_id,
                        term_num=0,
                        round_num=1
                    )
                )
            )

        my_vote: BroadcastConsensusVoteEvent = event_system.simulator._event_tasks.get_nowait()
        await sync_layer._on_sequence_vote(VoteSequence(
            my_vote.vote
        ))

        success_voter_count = success_vote_num -2

        for i in range(success_voter_count):
            await do_success_vote(validator_vote_factories[i])

        for i in range(none_vote_num):
            await do_none_vote(validator_vote_factories[success_voter_count + i])

        # TODO Count not vote
        for i in range(not_vote_num):
            await do_not_vote(voters[success_voter_count + none_vote_num + i])

        # THEN
        # DoneVoteEvent
        event_system.simulator._event_tasks.get_nowait()

        # BroadcastProposeEvent -> New Propose
        event_system.simulator._event_tasks.get_nowait()

        # Receive Event는 만들까 말까 고민중 (Gossip을 보아야 할듯?)
