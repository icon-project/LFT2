import json
from typing import Any, IO
from lft.event import EventSystem, AnyEvent, SerializableEvent


class EventRecorder:
    def __init__(self, event_system: EventSystem, io: IO):
        self.event_system = event_system
        self.number = 0
        self.io = io

        self._handler = None

    def __del__(self):
        self.close()

    def start(self):
        self.stop()
        self._handler = self.event_system.register_handler(AnyEvent, self.on_event_record)

    def stop(self):
        if self._handler:
            self.event_system.unregister_handler(AnyEvent, self._handler)
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
