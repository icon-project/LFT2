import pytest
from typing import Sequence
from lft.app.epoch import RotateEpoch
from lft.consensus.messages.data import Data
from lft.consensus.messages.vote import Vote


class MockData(Data):
    @property
    def id(self) -> bytes:
        return

    @property
    def prev_id(self) -> bytes:
        return

    @property
    def proposer_id(self) -> bytes:
        return self._leader

    @property
    def epoch_num(self) -> int:
        return

    @property
    def number(self) -> int:
        return

    @property
    def round_num(self) -> int:
        return self._round

    @property
    def prev_votes(self) -> Sequence[Vote]:
        return ()

    def is_lazy(self) -> bool:
        return False

    def is_none(self) -> bool:
        return False

    def __init__(self, leader, round_):
        self._leader = leader
        self._round = round_


@pytest.mark.parametrize("round_num,rotate_epoch,leader_num", [(0, 1, 0), (10, 1, 0), (13, 1, 3),
                                                              (2, 3, 0), (29, 3, 9), (70, 5, 4)])
def test_rotate_epoch(round_num, rotate_epoch, leader_num):
    validators = [b'0', b'1', b'2', b'3', b'4', b'5', b'6', b'7', b'8', b'9']
    epoch = RotateEpoch(0, rotate_bound=rotate_epoch, voters=validators)
    consensus_data_mock = MockData(leader=validators[leader_num], round_=round_num)
    epoch.verify_data(consensus_data_mock)
