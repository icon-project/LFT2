import asyncio
import random

from collections import defaultdict
from typing import TYPE_CHECKING, DefaultDict, Set
from lft.event import EventRegister, EventSimulator
from lft.consensus.events import (BroadcastDataEvent, BroadcastVoteEvent,
                                  ReceivedDataEvent, ReceivedVoteEvent, StartRoundEvent)


if TYPE_CHECKING:
    from lft.consensus.data import Data
    from lft.consensus.vote import Vote

Datums = DefaultDict[int, Set['Data']]
Votes = DefaultDict[int, Set['Vote']]


class Network(EventRegister):
    def __init__(self, event_simulator: EventSimulator):
        super().__init__(event_simulator)
        self._round_num = 0
        self._datums: Datums = defaultdict(set)
        self._votes: Votes = defaultdict(set)
        self._peers: Set['Network'] = set()

    def add_peer(self, peer: 'Network'):
        self._peers.add(peer)

    def remove_peer(self, peer: 'Network'):
        self._peers.remove(peer)

    def receive_data(self, data: 'Data'):
        self._datums[data.round_num].add(data)

        if data.round_num == self._round_num:
            event = ReceivedDataEvent(data)
            event.deterministic = False
            self._event_simulator.raise_event(event)

    def receive_vote(self, vote: 'Vote'):
        self._votes[vote.round_num].add(vote)

        if vote.round_num == self._round_num:
            event = ReceivedVoteEvent(vote)
            event.deterministic = False
            self._event_simulator.raise_event(event)

    def broadcast_data(self, data: 'Data'):
        loop = asyncio.get_event_loop()
        for peer in self._peers:
            delay = self.random_delay()
            loop.call_later(delay, peer.receive_data, data)

    def broadcast_vote(self, vote: 'Vote'):
        loop = asyncio.get_event_loop()
        for peer in self._peers:
            delay = self.random_delay()
            loop.call_later(delay, peer.receive_vote, vote)

    def _on_event_broadcast_data(self, event: 'BroadcastDataEvent'):
        self.broadcast_data(event.data)

    def _on_event_broadcast_vote(self, event: 'BroadcastVoteEvent'):
        self.broadcast_vote(event.vote)

    def _on_event_start_round(self, event: 'StartRoundEvent'):
        self._round_num = event.round_num
        for data in self._datums[event.round_num]:
            received_data_event = ReceivedDataEvent(data)
            self._event_simulator.raise_event(received_data_event)

        for vote in self._votes[event.round_num]:
            received_vote_event = ReceivedVoteEvent(vote)
            self._event_simulator.raise_event(received_vote_event)

    @classmethod
    def random_delay(cls):
        return random.randint(0, 10000) / 10000

    _handler_prototypes = {
        BroadcastDataEvent: _on_event_broadcast_data,
        BroadcastVoteEvent: _on_event_broadcast_vote,
        StartRoundEvent: _on_event_start_round
    }
