from typing import TYPE_CHECKING, List
from bisect import insort
from lft.consensus.layers.sync import SyncLayer
from lft.consensus.layers.round import RoundLayer


if TYPE_CHECKING:
    from lft.consensus.epoch import Epoch
    from lft.event import EventSystem
    from lft.consensus.messages.data import Data, DataFactory, DataPool
    from lft.consensus.messages.vote import Vote, VoteFactory, VotePool


class Round:
    def __init__(self, event_system: 'EventSystem', node_id: bytes, epoch: 'Epoch', round_num: int,
                 data_factory: 'DataFactory', vote_factory: 'VoteFactory', data_pool: 'DataPool', vote_pool: 'VotePool'):
        self._round_layer = RoundLayer(
            node_id, epoch, round_num, event_system, data_factory, vote_factory, data_pool, vote_pool
        )
        self._sync_layer = SyncLayer(
            self._round_layer, node_id, epoch, round_num, event_system, data_factory, vote_factory
        )

    @property
    def num(self):
        return self._sync_layer._round_num

    @property
    def epoch_num(self):
        return self._sync_layer._epoch.num

    @property
    def result_id(self):
        return self._round_layer.result_id

    @property
    def candidate_id(self):
        return self._round_layer._candidate_id

    @candidate_id.setter
    def candidate_id(self, new_candidate_id: bytes):
        self._round_layer._candidate_id = new_candidate_id

    async def round_start(self):
        await self._sync_layer.round_start()

    async def receive_data(self, data: 'Data'):
        await self._sync_layer.receive_data(data)

    async def receive_vote(self, vote: 'Vote'):
        await self._sync_layer.receive_vote(vote)

    def is_newer_than(self, epoch_num: int, round_num: int):
        if self.epoch_num == epoch_num:
            return self.num > round_num
        else:
            return self.epoch_num > epoch_num

    def is_older_than(self, epoch_num: int, round_num: int):
        if self.epoch_num == epoch_num:
            return self.num < round_num
        else:
            return self.epoch_num < epoch_num

    def is_equal_to(self, epoch_num: int, round_num: int):
        return self.epoch_num == epoch_num and self.num == round_num

    def __gt__(self, other: 'Round'):
        if not isinstance(other, Round):
            return False
        return self.is_newer_than(other.epoch_num, other.num)

    def __lt__(self, other: 'Round'):
        if not isinstance(other, Round):
            return False
        return self.is_older_than(other.epoch_num, other.num)


class RoundPool:
    def __init__(self):
        self._rounds: List[Round] = []

    def first_round(self):
        return self._rounds[0]

    def add_round(self, round_: Round):
        insort(self._rounds, round_)

    def get_round(self, epoch_num: int, round_num: int):
        try:
            return next(round_ for round_ in self._rounds
                        if round_.epoch_num == epoch_num and round_.num == round_num)
        except StopIteration:
            raise KeyError(epoch_num, round_num)

    def prune_round(self, latest_epoch_num: int, latest_round_num: int):
        self._rounds = [round_ for round_ in self._rounds
                        if (round_.is_newer_than(latest_epoch_num, latest_round_num) or
                            round_.is_equal_to(latest_epoch_num, latest_round_num))]

    def change_candidate(self):
        candidate_round = self.first_round()
        for round_ in self._rounds[1:]:
            round_.candidate_id = candidate_round.result_id
