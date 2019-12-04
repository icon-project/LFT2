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
from unittest import mock
from unittest.mock import MagicMock, Mock

from lft.app.data import DefaultData, DefaultDataFactory
from lft.app.epoch import RotateEpoch
from lft.app.vote import DefaultVoteFactory
from lft.consensus import Consensus
from lft.consensus.election import Election
from lft.consensus.messages.data import DataFactory, DataPool
from lft.consensus.messages.vote import VoteFactory, VotePool
from lft.consensus.round import Round, RoundPool
from lft.consensus.epoch import Epoch, EpochPool
from lft.event import EventSystem


async def setup_consensus():
    def _new_round_mock(self, epoch: 'Epoch', round_num: int, candidate_id: bytes):
        round_layer = MagicMock(Election(self._node_id, epoch, round_num, self._event_system,
                                self._data_factory, self._vote_factory, self._data_pool, self._vote_pool))
        new_round = MagicMock(Round(round_layer, self._node_id, epoch, round_num,
                              self._event_system, self._data_factory, self._vote_factory))
        new_round.candidate_id = candidate_id
        self._round_pool.add_round(new_round)
        return new_round

    Consensus._new_round = _new_round_mock

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

    consensus._epoch_pool = MagicMock(EpochPool())
    consensus._round_pool = MagicMock(RoundPool())
    consensus._data_pool = MagicMock(DataPool())
    consensus._vote_pool = MagicMock(VotePool())

    genesis_term = RotateEpoch(0, [])
    now_term = RotateEpoch(1, voters)

    genesis_data = DefaultData(
        id_=b"genesis",
        prev_id=None,
        proposer_id=None,
        number=0,
        epoch_num=0,
        round_num=0,
        prev_votes=[]
    )

    await consensus.initialize(genesis_term, now_term, 0, genesis_data, [])

    return consensus, voters, vote_factories, now_term, genesis_data
