import json
import coloredlogs
import logging
from lft.consensus.events import (Event, InitializeEvent, DoneRoundEvent,
                                  ReceivedDataEvent, ReceivedVoteEvent, StartRoundEvent,
                                  BroadcastDataEvent, BroadcastVoteEvent)
from lft.event import EventSimulator, EventRegister
from lft.serialization import Serializable


class Logger(EventRegister):
    def __init__(self, node_id: bytes, event_simulator: EventSimulator):
        super().__init__(event_simulator)
        self._node_id = node_id
        self._simulator = event_simulator
        self._encoder = _JSONEncoder()
        self._logger = logging.Logger(__name__)
        coloredlogs.install(level='DEBUG', milliseconds=True, logger=self._logger,
                            fmt='%(asctime)s,%(msecs)03d %(message)s',
                            datefmt='%H:%M:%S')

    def _print_log(self, event: Event):
        event_encoded = self._encoder.encode(event)
        event_serialized = json.loads(event_encoded)

        msg = self._make_log(event_serialized)
        self._logger.info(f"0x{shorten(self._node_id)} {msg}")

    def _make_log(self, event):
        if isinstance(event, dict):
            if "!type" in event:
                type_ = event["!type"].split(".")[-1]
                if "!data" in event:
                    return f"{type_}{self._make_log(event['!data'])}"
                else:
                    return f"{type_}"
            else:
                return "(" + ",".join(f"{k}={self._make_log(v)}" for k, v in event.items()) + ")"
        elif isinstance(event, list):
            return "[" + ",".join(self._make_log(item) for item in event) + "]"
        else:
            return f"{event}"

    _handler_prototypes = {
        InitializeEvent: _print_log,
        StartRoundEvent: _print_log,
        DoneRoundEvent: _print_log,
        ReceivedDataEvent: _print_log,
        ReceivedVoteEvent: _print_log,
        BroadcastDataEvent: _print_log,
        BroadcastVoteEvent: _print_log
    }


class _JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if not o:
            return "None"
        elif isinstance(o, bytes):
            return "0x" + shorten(o)
        elif isinstance(o, str):
            return "0r" + o
        elif isinstance(o, Serializable):
            return o.serialize()
        else:
            return super().encode(o)


def shorten(b: bytes):
    return b.hex()[:4]
