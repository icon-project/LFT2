import asyncio
from lft.app import Node
from lft.consensus.events import InitializeEvent


class App:
    def __init__(self, node_count: int):
        self.nodes = [Node() for _ in range(node_count)]

    def start(self):
        event = InitializeEvent(None, 0, None, tuple(node.id for node in self.nodes))
        for node in self.nodes:
            for peer in (peer for peer in self.nodes if peer != node):
                node.register_peer(peer.id, peer)

            node.event_system.simulator.raise_event(event)
            node.start(False)

        try:
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            print()
            print("Keyboard Interrupt")

