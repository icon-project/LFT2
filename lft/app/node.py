import os
from lft.app.communication import Gossiper
from lft.app.data import DefaultConsensusDataFactory, DefaultConsensusVoteFactory
from lft.app.logger import Logger
from lft.event import EventSystem
from lft.event.mediators import DelayedEventMediator
from lft.consensus.consensus import Consensus
from lft.consensus.data import ConsensusData, ConsensusVote
from lft.consensus.events import ReceivedConsensusDataEvent, ReceivedConsensusVoteEvent


class Node:
    def __init__(self):
        self.id = os.urandom(16)
        self.event_system = EventSystem()
        self.event_system.set_mediator(DelayedEventMediator)

        self.received_data = set()
        self.received_votes = set()

        self._gossipers = {}
        self._logger = Logger(self.id, self.event_system.simulator)
        self._consensus = Consensus(
            self.event_system,
            self.id,
            DefaultConsensusDataFactory(self.id),
            DefaultConsensusVoteFactory(self.id))

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
        self.event_system.start(blocking)

    def receive_data(self, data: ConsensusData):
        if data in self.received_data:
            print(f"{self.id} : receive data but ignored : {data}")
        else:
            print(f"{self.id} : receive data : {data}")
            self.received_data.add(data)

            event = ReceivedConsensusDataEvent(data)
            self.event_system.simulator.raise_event(event)

    def receive_vote(self, vote: ConsensusVote):
        if vote in self.received_votes:
            print(f"{self.id} : receive vote but ignored : {vote}")
        else:
            print(f"{self.id} : receive vote : {vote}")
            self.received_votes.add(vote)

            event = ReceivedConsensusVoteEvent(vote)
            self.event_system.simulator.raise_event(event)

    def register_peer(self, peer_id: bytes, peer: 'Node'):
        gossiper = Gossiper(self.event_system, self, peer)
        self._gossipers[peer_id] = gossiper

    def unregister_peer(self, peer_id: bytes):
        self._gossipers.pop(peer_id, None)
