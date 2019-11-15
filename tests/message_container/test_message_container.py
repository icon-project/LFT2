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
from lft.consensus.candidate import Candidate
from lft.consensus.layers.order import OrderMessages


@pytest.mark.asyncio
async def test_candidate_change_by_vote():
    # GIVEN
    order_messages, nodes = init_container()
    candidate = DefaultData(
        id_=b'first',
        prev_id=b'',
        proposer_id=nodes[1],
        number=0,
        term_num=0,
        round_num=1,
        prev_votes=[]
    )
    order_messages.add_data(candidate)

    votes = await _create_votes(nodes, candidate)
    for vote in votes:
        order_messages.add_vote(vote)
    # WHEN
    changed_candidate = order_messages.get_reach_candidate(0, 1, b'first')
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
    order_messages, nodes = init_container()
    candidate = DefaultData(
        id_=b'first',
        prev_id=b'genesis',
        proposer_id=nodes[2],
        number=1,
        term_num=0,
        round_num=2,
        prev_votes=[]
    )

    order_messages.add_data(candidate)
    votes = await _create_votes(nodes, candidate)
    for vote in votes:
        order_messages.add_vote(vote)

    # WHEN
    changed_candidate = order_messages.get_reach_candidate(candidate.term_num, candidate.round_num, candidate.id)
    # THEN
    assert candidate == changed_candidate.data
    assert votes == list(changed_candidate.votes)


@pytest.mark.asyncio
async def test_raise_block_sync_by_vote():

    order_messages, nodes = init_container()
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
        order_messages.add_vote(vote)

    # WHEN
    try:
        changed_candidate = order_messages.get_reach_candidate(candidate.term_num, candidate.round_num, candidate.id)
    except NeedSync as e:
        assert e.new_candidate_id == b'first'
        assert e.old_candidate_id == b'genesis'
    else:
        pytest.fail("Should raise NeedSync")


@pytest.mark.asyncio
async def test_candidate_change_prev_term_data():
    order_messages, nodes = init_container()
    new_nodes = [b'4', b'0', b'6', b'7', b'8', b'9', b'10', b'11']
    candidate = DefaultData(
        id_=b'first',
        prev_id=b'',
        proposer_id=nodes[1],
        number=0,
        term_num=0,
        round_num=1,
        prev_votes=[]
    )
    order_messages.add_data(candidate)

    # WHEN
    new_term = RotateTerm(1, new_nodes)
    order_messages.update_term(new_term)

    votes = await _create_votes(nodes, candidate)
    for vote in votes:
        order_messages.add_vote(vote)

    changed_candidate = order_messages.get_reach_candidate(0, 1, b'first')
    # THEN
    assert candidate == changed_candidate.data
    assert votes == list(changed_candidate.votes)


@pytest.mark.asyncio
async def test_candidate_change_connected_prev_term_data():
    order_messages, nodes = init_container()
    new_nodes = [b'4', b'0', b'6', b'7', b'8', b'9', b'10', b'11']
    candidate = DefaultData(
        id_=b'first',
        prev_id=b'genesis',
        proposer_id=nodes[2],
        number=1,
        term_num=0,
        round_num=2,
        prev_votes=[]
    )
    order_messages.add_data(candidate)

    # WHEN
    new_term = RotateTerm(1, new_nodes)
    order_messages.update_term(new_term)

    votes = await _create_votes(nodes, candidate)
    for vote in votes:
        order_messages.add_vote(vote)

    changed_candidate = order_messages.get_reach_candidate(0, 2, b'first')
    # THEN
    assert candidate == changed_candidate.data
    assert votes == list(changed_candidate.votes)


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
    order_messages = OrderMessages(None, term, Candidate(genesis_data, []))
    return order_messages, nodes
