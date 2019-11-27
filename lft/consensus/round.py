from typing import TYPE_CHECKING, Sequence
from lft.consensus.layers.sync import SyncLayer
from lft.consensus.layers.round import RoundLayer


if TYPE_CHECKING:
    from lft.consensus.term import Term
    from lft.event import EventSystem
    from lft.consensus.messages.data import Data, DataFactory, DataPool
    from lft.consensus.messages.vote import Vote, VoteFactory, VotePool


class Round:
    def __init__(self, event_system: 'EventSystem', node_id: bytes,
                 data_factory: 'DataFactory', vote_factory: 'VoteFactory',
                 data_pool: 'DataPool', vote_pool: 'VotePool'):
        self._round_layer = RoundLayer(node_id, event_system, data_factory, vote_factory, data_pool, vote_pool)
        self._sync_layer = SyncLayer(self._round_layer, node_id, event_system, data_factory, vote_factory)

    @property
    def num(self):
        return self._sync_layer._round_num

    @property
    def term_num(self):
        return self._sync_layer._term.num

    @property
    def result_id(self):
        return self._round_layer.result_id

    @property
    def candidate_id(self):
        return self._round_layer._candidate_id

    @candidate_id.setter
    def candidate_id(self, new_candidate_id: bytes):
        self._round_layer._candidate_id = new_candidate_id

    async def round_start(self, term: 'Term', round_num: int):
        await self._sync_layer.round_start(term, round_num)

    async def receive_data(self, data: 'Data'):
        await self._sync_layer.receive_data(data)

    async def receive_vote(self, vote: 'Vote'):
        await self._sync_layer.receive_vote(vote)

    def is_newer_than(self, term_num: int, round_num: int):
        if self.term_num == term_num:
            return self.num > round_num
        else:
            return self.term_num > term_num

    def is_older_than(self, term_num: int, round_num: int):
        if self.term_num == term_num:
            return self.num < round_num
        else:
            return self.term_num < term_num

    def is_equal_to(self, term_num: int, round_num: int):
        return self.term_num == term_num and self.num == round_num
