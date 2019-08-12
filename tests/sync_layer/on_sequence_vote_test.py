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

from lft.consensus.default_data.data import DefaultConsensusData
from lft.consensus.default_data.factories import DefaultConsensusVoteFactory
from lft.consensus.events import DoneRoundEvent, ProposeSequence, VoteSequence, BroadcastConsensusVoteEvent, \
    BroadcastConsensusDataEvent, ReceivedConsensusDataEvent, ReceivedConsensusVoteEvent
from lft.consensus.factories import ConsensusVoteFactory, ConsensusData
from lft.event import Event
from tests.sync_layer.setup_sync_layer import setup_sync_layer, CANDIDATE_ID, LEADER_ID, TEST_NODE_ID

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
    async def on_vote_test():
        print("aaa")
        event_system, sync_layer, prev_voters, genesis_data = await setup_sync_layer(QUORUM)
        success_propose_is_come = success_vote_num != 0

        consensus_data = None
        if success_propose_is_come:
            consensus_data = DefaultConsensusData(
                id_=PROPOSE_ID,
                prev_id=CANDIDATE_ID,
                proposer_id=LEADER_ID,
                number=1,
                term_num=0,
                round_num=1,
                prev_votes=None
            )
        else:
            consensus_data = DefaultConsensusData(
                id_=LEADER_ID,
                prev_id=LEADER_ID,
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

        prev_voters.remove(LEADER_ID)
        prev_voters.remove(TEST_NODE_ID)
        validator_vote_factories = [DefaultConsensusVoteFactory(x) for x in prev_voters]

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

        my_vote: ReceivedConsensusVoteEvent = await get_event(event_system)
        my_vote: BroadcastConsensusVoteEvent = await get_event(event_system)
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
            await do_not_vote(prev_voters[success_voter_count + none_vote_num + i])

        # THEN
        if is_complete:
            done_round: DoneRoundEvent = await get_event(event_system)
            if is_success:
                assert done_round.is_success
                check_round_num(done_round)
                assert done_round.candidate_data == consensus_data
                assert done_round.commit_data == genesis_data

                broadcast_propose: BroadcastConsensusDataEvent = await get_event(event_system)
                check_new_consensus_data(broadcast_propose.data, consensus_data.id, 2)
                check_prev_votes(broadcast_propose.data.prev_votes, consensus_data)

                receive_propose: ReceivedConsensusDataEvent = await get_event(event_system)

                check_new_consensus_data(receive_propose.data, consensus_data.id, 2)
                check_prev_votes(receive_propose.data.prev_votes, consensus_data)
            else:
                assert not done_round.is_success
                check_round_num(done_round)
                assert not done_round.candidate_data
                assert not done_round.commit_data
                broadcast_propose: BroadcastConsensusDataEvent = await get_event(event_system)
                check_new_consensus_data(broadcast_propose.data, genesis_data.id, 1)
                receive_propose: ReceivedConsensusDataEvent = await get_event(event_system)
                check_new_consensus_data(receive_propose.data, genesis_data.id, 1)

        with pytest.raises(QueueEmpty):
            await get_event(event_system)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(on_vote_test())


async def get_event(event_system) -> Event:
    non_deterministic, mono_ns, event = event_system.simulator._event_tasks.get_nowait()
    return event


def check_round_num(done_round):
    assert done_round.round_num == 1
    assert done_round.term_num == 0


def check_new_consensus_data(data: ConsensusData, prev_id, number):
    assert data.proposer_id == TEST_NODE_ID
    assert data.term_num == 0
    assert data.round_num == 2
    assert data.prev_id == prev_id

    assert data.number == number


def check_prev_votes(prev_votes, consensus_data):
    prev_voters = []
    for vote in prev_votes:
        assert vote.data_id == consensus_data.id
        assert vote.voter_id not in prev_voters
        prev_voters.append(vote.voter_id)
