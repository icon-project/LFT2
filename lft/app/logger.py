import datetime
import json
from lft.consensus.events import (Event, InitializeEvent, DoneRoundEvent,
                                  ReceivedDataEvent, ReceivedVoteEvent, StartRoundEvent,
                                  ProposeSequence, VoteSequence, BroadcastDataEvent,
                                  BroadcastVoteEvent)
from lft.event import EventSimulator, EventRegister
from lft.serialization import Serializable


class Logger(EventRegister):
    def __init__(self, node_id: bytes, event_simulator: EventSimulator):
        super().__init__(event_simulator)
        self._node_id = node_id
        self._simulator = event_simulator
        self._encoder = _JSONEncoder()

    def _print_log(self, event: Event):
        event_serialized = self._encoder.encode(event)
        print(f"{shorten(self._node_id)}, {datetime.datetime.now()}:: {event_serialized}")

    _handler_prototypes = {
        InitializeEvent: _print_log,
        StartRoundEvent: _print_log,
        DoneRoundEvent: _print_log,
        ReceivedDataEvent: _print_log,
        ReceivedVoteEvent: _print_log,
        ProposeSequence: _print_log,
        VoteSequence: _print_log,
        BroadcastDataEvent: _print_log,
        BroadcastVoteEvent: _print_log
    }


class _JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, bytes):
            return "0x" + shorten(o)
        elif isinstance(o, str):
            return "0r" + o
        elif isinstance(o, Serializable):
            return o.serialize()
        else:
            return super().encode(o)


def shorten(b: bytes):
    return b.hex()[:8]
