import asyncio
import os
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import List
from lft.app import Node
from lft.consensus.events import InitializeEvent

RECORD_PATH = "record.log"


class App(ABC):
    def start(self):
        nodes = self._gen_nodes()
        for node in nodes:
            for peer in (peer for peer in nodes if peer != node):
                node.register_peer(peer.id, peer)
        self._start(nodes)
        self._run_forever(nodes)

    @abstractmethod
    def _start(self, nodes: List[Node]):
        raise NotImplementedError

    @abstractmethod
    def _gen_nodes(self) -> List[Node]:
        raise NotImplementedError

    def _run_forever(self, nodes: List[Node]):
        try:
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            print()
            print("Keyboard Interrupt")
        finally:
            for node in nodes:
                node.close()


class InstantApp(App):
    def __init__(self, number: int):
        self.number = number

    def _start(self, nodes: List[Node]):
        for node in nodes:
            node.start(False)

            event = InitializeEvent(0, 0, None, tuple(node.id for node in nodes))
            event.deterministic = False
            node.event_system.simulator.raise_event(event)

    def _gen_nodes(self) -> List[Node]:
        return [Node(os.urandom(16)) for _ in range(self.number)]


class RecordApp(App):
    def __init__(self, number: int, path: Path):
        self.number = number
        self.path = path

    def _start(self, nodes: List[Node]):
        for node in nodes:
            node_path = self.path.joinpath(node.id.hex())
            node_path.mkdir()

            record_io = open(str(node_path.joinpath(RECORD_PATH)), 'w')
            node.start_record(record_io, blocking=False)

            event = InitializeEvent(0, 0, None, tuple(node.id for node in nodes))
            event.deterministic = False
            node.event_system.simulator.raise_event(event)

    def _gen_nodes(self) -> List[Node]:
        self.path.mkdir(parents=True, exist_ok=True)
        return [Node(os.urandom(16)) for _ in range(self.number)]


class ReplayApp(App):
    def __init__(self, path: Path, node: bytes):
        self.path = path
        self.node = node

    def _gen_nodes(self) -> List[Node]:
        return [Node(self.node)]

    def _get_nodes_id(self):
        return [Path(path) for path in os.listdir(str(self.path))]

    def _start(self, nodes: List[Node]):
        for node in nodes:
            node_path = self.path.joinpath(node.id.hex())
            record_io = open(str(node_path.joinpath(RECORD_PATH)), 'r')

            node.start_replay(record_io, blocking=False)


class Mode(Enum):
    instant = "instant"
    record = "record"
    replay = "replay"

