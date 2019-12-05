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
from tests.consensus.mocks import RoundMock


async def setup_consensus():
    def _new_round_mock(self, epoch: 'Epoch', round_num: int, candidate_id: bytes):
        new_round = RoundMock(epoch, round_num)
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
