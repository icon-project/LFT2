import os
from lft.app import Node
from lft.event import EventRegister
from lft.consensus.events import RoundStartEvent, ReceiveDataEvent, BroadcastDataEvent


class DoubleProposer(EventRegister):
    def __init__(self, node: Node):
        super().__init__(node.event_system.simulator)
        self.node = node
        self.consensus = node._consensus
        self.epoch_pool = self.consensus._epoch_pool
        self.round_pool = self.consensus._round_pool
        self.data_pool = self.consensus._data_pool
        self.vote_pool = self.consensus._vote_pool
        self.data_factory = self.consensus._data_factory
        self.vote_factory = self.consensus._vote_factory

        self._started = False

    def start(self):
        self._started = True

    def stop(self):
        self._started = False

    async def round_start(self, event: RoundStartEvent):
        if self._started:
            await self.propose(event.epoch.num, event.round_num)

    async def propose(self, epoch_num: int, round_num: int):
        prev_id = self.round_pool.first_round().result_id
        prev_data = self.data_pool.get_data(prev_id)
        prev_epoch = self.epoch_pool.get_epoch(prev_data.epoch_num)
        prev_votes = self.vote_pool.get_votes(prev_data.epoch_num, prev_data.round_num)
        prev_votes = {vote.voter_id: vote for vote in prev_votes if vote.data_id == prev_id}
        prev_votes = tuple(prev_votes[voter] if voter in prev_votes else None
                           for voter in prev_epoch.voters)

        fake_data = await self.data_factory.create_data(prev_data.number + 1, prev_id, epoch_num, round_num, prev_votes)
        fake_data._id = os.urandom(16)

        event = BroadcastDataEvent(fake_data)
        event.deterministic = False
        self._event_simulator.raise_event(event)

        event = ReceiveDataEvent(fake_data)
        event.deterministic = False
        self._event_simulator.raise_event(event)

    _handler_prototypes = {
        RoundStartEvent: round_start,
    }
