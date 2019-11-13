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
from lft.app.term import RotateTerm
from lft.app.vote import DefaultVoteFactory
from lft.consensus.messages.data import Data
from lft.consensus.exceptions import NeedSync
from lft.consensus.layers.order_layer import MessageContainer
from lft.consensus.round import Candidate


@pytest.mark.asyncio
async def test_candidate_change_by_vote():
    # GIVEN
    message_container, nodes = init_container()
    candidate = DefaultData(
        id_=b'first',
        prev_id=b'',
        proposer_id=nodes[1],
        number=0,
        term_num=0,
        round_num=1,
        prev_votes=[]
    )
    message_container.add_data(candidate)

    votes = await _create_votes(nodes, candidate)
    for vote in votes:
        message_container.add_vote(vote)
    # WHEN
    changed_candidate = message_container.get_reach_candidate(0, 1, b'first')
    # THEN
    assert candidate == changed_candidate.data
    assert votes == list(changed_candidate.votes)


async def _create_votes(nodes, candidate: Data):
    votes = []
    for i, node in enumerate(nodes):
        vote_factory = DefaultVoteFactory(node)
        vote = await vote_factory.create_vote(candidate.id, candidate.prev_id, candidate.term_num, candidate.round_num)
        votes.append(vote)
    return votes


@pytest.mark.asyncio
async def test_candidate_change_by_candidate_connected_vote():
    # GIVEN
    message_container, nodes = init_container()
    candidate = DefaultData(
        id_=b'first',
        prev_id=b'genesis',
        proposer_id=nodes[2],
        number=1,
        term_num=0,
        round_num=2,
        prev_votes=[]
    )

    message_container.add_data(candidate)
    votes = await _create_votes(nodes, candidate)
    for vote in votes:
        message_container.add_vote(vote)

    # WHEN
    changed_candidate = message_container.get_reach_candidate(candidate.term_num, candidate.round_num, candidate.id)
    # THEN
    assert candidate == changed_candidate.data
    assert votes == list(changed_candidate.votes)


@pytest.mark.asyncio
async def test_raise_block_sync_by_vote():

    message_container, nodes = init_container()
    candidate = DefaultData(
        id_=b'first',
        prev_id=b'',
        proposer_id=nodes[1],
        number=0,
        term_num=0,
        round_num=1,
        prev_votes=[]
    )
    votes = await _create_votes(nodes, candidate)
    for vote in votes:
        message_container.add_vote(vote)

    # WHEN
    try:
        changed_candidate = message_container.get_reach_candidate(candidate.term_num, candidate.round_num, candidate.id)
    except NeedSync as e:
        assert e.new_candidate_id == b'first'
        assert e.old_candidate_id == b'genesis'
    else:
        pytest.fail("Should raise NeedSync")


def init_container():
    nodes = [b'0', b'1', b'2', b'3']
    genesis_data = DefaultData(
        id_=b'genesis',
        prev_id=b'',
        proposer_id=nodes[0],
        number=0,
        term_num=0,
        round_num=0,
        prev_votes=[]
    )
    term = RotateTerm(0, nodes)
    message_container = MessageContainer(term, Candidate(genesis_data, []))
    return message_container, nodes
