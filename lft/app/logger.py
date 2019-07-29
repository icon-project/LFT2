import json
from lft.consensus.events import (Event, InitializeEvent, DoneRoundEvent,
                                  ReceivedConsensusDataEvent, ReceivedConsensusVoteEvent)
from lft.event import EventSimulator


class Logger:
    def __init__(self, node_id: bytes, event_simulator: EventSimulator):
        self._node_id = node_id
        self._simulator = event_simulator
        self._encoder = JSONEncoder()

        self._handlers = {
            InitializeEvent:
                self._simulator.register_handler(InitializeEvent, self._on_initialize_event),
            DoneRoundEvent:
                self._simulator.register_handler(DoneRoundEvent, self._on_done_round_event),
            ReceivedConsensusDataEvent:
                self._simulator.register_handler(ReceivedConsensusDataEvent, self._on_received_consensus_data_event),
            ReceivedConsensusVoteEvent:
                self._simulator.register_handler(ReceivedConsensusVoteEvent, self._on_received_consensus_vote_event)
        }

    def __del__(self):
        self.close()

    def close(self):
        for event_type, handler in self._handlers.items():
            self._simulator.unregister_handler(event_type, handler)
        self._handlers.clear()

    def _on_initialize_event(self, event: InitializeEvent):
        self._print_log(event)

    def _on_done_round_event(self, event: DoneRoundEvent):
        self._print_log(event)

    def _on_received_consensus_data_event(self, event: ReceivedConsensusDataEvent):
        self._print_log(event)

    def _on_received_consensus_vote_event(self, event: ReceivedConsensusVoteEvent):
        self._print_log(event)

    def _print_log(self, event: Event):
        event_serialized = self._encoder.encode(event.serialize())
        event_serialized = event_serialized.replace("\\", "").replace("lft.consensus.events.", "")
        print(f"{shorten(self._node_id)}, {event_serialized}")


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, bytes):
            return shorten(o)
        if isinstance(o, list) or isinstance(o, dict):
            return super().encode(o)
        return self.encode(o.__dict__)


def shorten(b: bytes):
    return b.hex()[:8]
