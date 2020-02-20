from mock import MagicMock
from functools import partial

from lft.app.data import DefaultData, DefaultDataFactory
from lft.app.epoch import RotateEpoch
from lft.app.vote import DefaultVoteFactory
from lft.consensus import Consensus
from lft.event import EventSystem
from tests.units.consensus.mocks import RoundMock


async def setup_consensus():
    def _new_round_mock(self, epoch_num: int, round_num: int, candidate_id: bytes):
        epoch = self._get_epoch(epoch_num)
        new_round = RoundMock(epoch, round_num)
        new_round.candidate_id = candidate_id
        self._round_pool.add_round(new_round)
        return new_round

    voters = [bytes([x]) for x in range(4)]
    vote_factories = [DefaultVoteFactory(voter) for voter in voters]

    event_system = MagicMock(EventSystem())
    data_factory = MagicMock(DefaultDataFactory(voters[0]))
    vote_factory = MagicMock(DefaultVoteFactory(voters[0]))
    consensus = Consensus(event_system,
                          voters[0],
                          data_factory,
                          vote_factory)
    consensus._new_round = partial(_new_round_mock, consensus)

    genesis_epoch = RotateEpoch(0, [])
    now_epoch = RotateEpoch(1, voters)
    epochs = [genesis_epoch, now_epoch]

    genesis_data = DefaultData(
        id_=b"genesis",
        prev_id=None,
        proposer_id=None,
        number=0,
        epoch_num=0,
        round_num=0,
        prev_votes=[]
    )

    datums = [genesis_data]
    votes = []

    await consensus.initialize(commit_id=genesis_data.prev_id, epoch_pool=epochs, data_pool=datums, vote_pool=votes)
    return consensus, voters, vote_factories, now_epoch, genesis_data
