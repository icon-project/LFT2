import os
from lft.app.communication import Gossiper
from lft.event import EventSystem
from lft.event.mediators import DelayedEventMediator
from lft.consensus.consensus import Consensus
from lft.consensus.factories import ConsensusData, ConsensusVote
from lft.consensus.events import ReceivedConsensusDataEvent, ReceivedConsensusVoteEvent


class Node:
    def __init__(self):
        self.id = os.urandom(16)
        self.event_system = EventSystem()
        self.event_system.set_mediator(DelayedEventMediator)

        self.received_blocks = set()
        self.received_votes = set()

        self._consensus = Consensus(self.event_system, self.id, None, None)
        self._gossipers = {}

    def __del__(self):
        self.close()

    def close(self):
        for gossiper in self._gossipers:
            gossiper.close()
        self._gossipers.clear()

        if self._consensus:
            self._consensus.close()
            self._consensus = None

    def start(self, blocking=True):
        self.event_system.simulator.start(blocking)

    def receive_block(self, block: ConsensusData):
        if block in self.received_blocks:
            print(f"{self.id} : receive block but ignored : {block}")
        else:
            print(f"{self.id} : receive_block : {block}")
            self.received_blocks.add(block)

            event = ReceivedConsensusDataEvent(block)
            self.event_system.simulator.raise_event(event)

    def receive_vote(self, vote: ConsensusVote):
        if vote in self.received_votes:
            print(f"{self.id} : receive vote but ignored : {vote}")
        else:
            print(f"{self.id} : receive_block : {vote}")
            self.received_votes.add(vote)

            event = ReceivedConsensusVoteEvent(vote)
            self.event_system.simulator.raise_event(event)

    def register_peer(self, peer_id: bytes, peer: 'Node'):
        gossiper = Gossiper(self.event_system, self, peer)
        self._gossipers[peer_id] = gossiper

    def unregister_peer(self, peer_id: bytes):
        self._gossipers.pop(peer_id, None)
