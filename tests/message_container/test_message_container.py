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
from lft.app.vote import DefaultVote, DefaultVoteFactory
from lft.consensus.exceptions import ReachCandidate, NeedSync
from lft.consensus.layers.order_layer import MessageContainer


@pytest.mark.asyncio
async def test_candidate_change_by_vote():
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
    # Term을 가지고 있는게 나을듯
    for i, node in enumerate(nodes):
        vote_factory = DefaultVoteFactory(node)
        vote = await vote_factory.create_vote(b'first', b'', 0, 1)
        if i == 2:
            try:
                message_container.add_vote(vote)
            except ReachCandidate as e:
                assert e.candidate == candidate
                assert message_container.candidate_data == candidate
            else:
                pytest.fail("Should raise ReachCandidate")
        else:
            message_container.add_vote(vote)


@pytest.mark.asyncio
async def test_candidate_change_by_data():
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
    # Term을 가지고 있는게 나을듯
    prev_votes = []
    for i, node in enumerate(nodes):
        vote_factory = DefaultVoteFactory(node)
        vote = await vote_factory.create_vote(b'first', b'', 0, 1)
        prev_votes.append(vote)

    try:
        message_container.add_data(
            DefaultData(
                id_=b'second',
                prev_id=b'first',
                proposer_id=nodes[2],
                number=1,
                term_num=0,
                round_num=1,
                prev_votes=prev_votes
            )
        )
    except ReachCandidate as e:
        assert e.candidate == candidate
        assert message_container.candidate_data == candidate
    else:
        pytest.fail("Should raise NeedSync")


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
    for i, node in enumerate(nodes):
        vote_factory = DefaultVoteFactory(node)
        vote = await vote_factory.create_vote(b'first', b'', 0, 1)
        if i == 2:
            try:
                message_container.add_vote(vote)
            except NeedSync as e:
                assert e.new_candidate_id == b'first'
                assert e.old_candidate_id == b'genesis'
            else:
                pytest.fail("Should raise NeedSync")
        else:
            message_container.add_vote(vote)


@pytest.mark.asyncio
async def test_raise_block_sync_by_data():
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
    prev_votes = []
    for i, node in enumerate(nodes):
        vote_factory = DefaultVoteFactory(node)
        vote = await vote_factory.create_vote(b'first', b'', 0, 1)
        prev_votes.append(vote)

    try:
        message_container.add_data(
            DefaultData(
                id_=b'second',
                prev_id=b'first',
                proposer_id=nodes[2],
                number=1,
                term_num=0,
                round_num=1,
                prev_votes=prev_votes
            )
        )
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
    message_container = MessageContainer(term, genesis_data)
    return message_container, nodes
