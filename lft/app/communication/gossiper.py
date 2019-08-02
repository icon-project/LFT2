import asyncio
import random
from typing import TYPE_CHECKING
from lft.event import EventSystem
from lft.consensus.factories import ConsensusData, ConsensusVote
from lft.consensus.events import ProposeSequence, VoteSequence


if TYPE_CHECKING:
    from lft.app import Node

TIME_SLEEP = 0.1
TIME_TO_LIVE = 5


class Gossiper:
    def __init__(self, event_system: EventSystem, sender: 'Node', receiver: 'Node'):
        self._event_system = event_system
        self._sender = sender
        self._receiver = receiver

        self._cached_data = set()
        self._cached_votes = set()

        self._reserved_data = set()
        self._reserved_votes = set()

        self._asset_data = set()
        self._asset_votes = set()

        simulator = event_system.simulator
        self._handlers = {
            ProposeSequence:
                simulator.register_handler(ProposeSequence, self._on_propose_sequence),
            VoteSequence:
                simulator.register_handler(VoteSequence, self._on_vote_sequence)
        }

    def __del__(self):
        self.close()

    def close(self):
        for event_type, handler in self._handlers.items():
            self._event_system.simulator.unregister_handler(event_type, handler)
        self._handlers.clear()

    def _send_data(self, data: ConsensusData):
        delay = self._get_random_delay()
        asyncio.get_event_loop().call_later(delay, self._receiver.receive_data, data)

    def _send_vote(self, vote: ConsensusVote):
        delay = self._get_random_delay()
        asyncio.get_event_loop().call_later(delay, self._receiver.receive_vote, vote)

    def _on_propose_sequence(self, event: ProposeSequence):
        if event.data.is_not():
            return
        if event.data in self._cached_data:
            return

        self._cached_data.add(event.data)
        self._reserved_data.add(event.data)
        self._asset_data.add(event.data)
        asyncio.get_event_loop().call_later(TIME_TO_LIVE, self._cached_data.remove, event.data)

    def _on_vote_sequence(self, event: VoteSequence):
        if event.vote.is_not():
            return
        if event.vote in self._cached_votes:
            return

        self._cached_votes.add(event.vote)
        self._reserved_votes.add(event.vote)
        self._asset_data.add(event.vote)
        asyncio.get_event_loop().call_later(TIME_TO_LIVE, self._cached_votes.remove, event.vote)

    async def _gossip(self):
        while True:
            for data in self._reserved_data:
                self._send_data(data)
            self._reserved_data.clear()

            for vote in self._reserved_votes:
                self._send_vote(vote)
            self._reserved_votes.clear()

            missing_data = self._asset_data - self._receiver.received_data
            for data in missing_data:
                self._send_data(data)

            missing_votes = self._asset_votes - self._receiver.received_votes
            for vote in missing_votes:
                self._send_vote(vote)

            await asyncio.sleep(0.1)

    @classmethod
    def _get_random_delay(cls):
        r = random.randint(0, 100)
        if r < 1:
            return 2 ** 32
        elif r < 5:
            return random.randint(0, 10000) / 100
        else:
            return random.randint(0, 10000) / 10000

