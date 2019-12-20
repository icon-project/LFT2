import os
from lft.app import Node
from lft.event import EventRegister
from lft.consensus.messages.data import Data
from lft.consensus.events import ReceiveVoteEvent, ReceiveDataEvent, BroadcastVoteEvent


class DoubleVoter(EventRegister):
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

    async def receive_data(self, event: ReceiveDataEvent):
        if self._started:
            self.vote(event.data)

    def vote(self, data: Data):
        none_vote = self.vote_factory.create_none_vote(data.epoch_num, data.round_num)

        event = BroadcastVoteEvent(none_vote)
        event.deterministic = False
        self._event_simulator.raise_event(event)

        event = ReceiveVoteEvent(none_vote)
        event.deterministic = False
        self._event_simulator.raise_event(event)

    _handler_prototypes = {
        ReceiveDataEvent: receive_data
    }
