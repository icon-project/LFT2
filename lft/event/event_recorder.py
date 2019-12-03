import os
from typing import Any, IO
from lft.event import EventSimulator, Event, AnyEvent
from lft.serialization import Serializer, Serializable

__all__ = ("EventRecorder", )


class EventRecorder:
    def __init__(self, event_simulator: EventSimulator):
        self.event_simulator = event_simulator
        self.number = 0
        self.io: IO = None

        self._serializer = Serializer()
        self._handler = None

    def __del__(self):
        self.close()

    def start(self, io: IO):
        self.stop()
        self.io = io
        self._handler = self.event_simulator.register_handler(AnyEvent, self.on_event_record)

    def stop(self):
        if self._handler:
            self.event_simulator.unregister_handler(AnyEvent, self._handler)
            self._handler = None

    def close(self):
        self.stop()
        if self.io and not self.io.closed:
            self.io.close()
            self.io = None

    def on_event_record(self, event: Any):
        if not event.deterministic:
            record = EventRecord(self.number, event)
            record_serialized = self._serializer.serialize(record)
            self.io.write(record_serialized)
            self.io.write(os.linesep)
        self.number += 1


class EventRecord(Serializable):
    def __init__(self, number: int, event: Event):
        self.number = number
        self.event = event
