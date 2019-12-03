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
from unittest.mock import MagicMock

from lft.app.data import DefaultData, DefaultDataFactory
from lft.app.term import RotateTerm
from lft.app.vote import DefaultVoteFactory
from lft.consensus import Consensus
from lft.consensus.messages.data import DataFactory
from lft.consensus.messages.vote import VoteFactory
from lft.consensus.round import Round
from lft.consensus.term import Term
from lft.event import EventSystem


async def setup_consensus():
    voters = [bytes([x]) for x in range(4)]
    vote_factories = [DefaultVoteFactory(voter) for voter in voters]

    event_system = MagicMock(EventSystem())
    data_factory = MagicMock(DefaultDataFactory(voters[0]))
    vote_factory = MagicMock(DefaultVoteFactory(voters[0]))
    consensus = Consensus(event_system,
                          voters[0],
                          data_factory,
                          vote_factory
                          )

    genesis_term = RotateTerm(0, [])
    now_term = RotateTerm(1, voters)

    genesis_data = DefaultData(
        id_=b"genesis",
        prev_id=None,
        proposer_id=None,
        number=0,
        term_num=0,
        round_num=0,
        prev_votes=[]
    )

    def new_round_mock(self: Consensus, term: 'Term', round_num: int, candidate_id: bytes):
        new_round = MagicMock(Round(self._event_system, self._node_id, term, round_num,
                              self._data_factory, self._vote_factory, self._data_pool, self._vote_pool))
        new_round.candidate_id = candidate_id
        self._round_pool.add_round(new_round)
        return new_round

    consensus._new_round = new_round_mock
    await consensus.initialize(genesis_term, now_term, 0, genesis_data, [])

    return consensus, voters, vote_factories, now_term, genesis_data
