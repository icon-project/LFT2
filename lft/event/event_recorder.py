import json
import os
from typing import Any, IO
from lft.event import EventSimulator, AnyEvent, SerializableEvent


class EventRecorder:
    def __init__(self, event_simulator: EventSimulator):
        self.event_simulator = event_simulator
        self.number = 0
        self.io: IO = None

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
        if not event.deterministic and isinstance(event, SerializableEvent):
            record = EventRecord(self.number, event)
            record_serialized = record.serialize()
            self.io.write(json.dumps(record_serialized))
            self.io.write(os.linesep)
        self.number += 1


class EventRecord:
    def __init__(self, number: int, event: SerializableEvent):
        self.number = number
        self.event = event

    def serialize(self):
        return {
            "number": self.number,
            "event_type": type(self.event).__name__,
            "event_contents": self.event.serialize()
        }

    @classmethod
    def deserialize(cls, record_serialized: dict):
        event_type_name = record_serialized["event_type"]
        event_type = SerializableEvent.types[event_type_name]

        return EventRecord(
            record_serialized["number"],
            event_type.deserialize(record_serialized["event_contents"])
        )
