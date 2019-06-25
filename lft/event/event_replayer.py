import json
from typing import Iterator, IO
from lft.event import EventSystem, EventRecord, Event, AnyEvent


class EventReplayer:
    def __init__(self, event_system: EventSystem):
        self._event_system = event_system
        self._number = -1  # EventReplayer raises a trash event first to start event system
        self._record: EventRecord = None
        self._records: IO = None
        self._handler = None

    def __del__(self):
        self.stop()

    def start(self, records: IO):
        self.stop()

        self._records = records
        self._handler = self._event_system.register_handler(AnyEvent, self.on_event_replay)
        self._event_system.raise_event(AnyEvent())

    def stop(self):
        if self._handler:
            self._event_system.unregister_handler(AnyEvent, self._handler)
            self._handler = None

    def close(self):
        self.stop()
        if self._records and not self._records.closed:
            self._records.close()

    def on_event_replay(self, event: Event):
        self._record = self._get_record_if_not_exist()
        if self._record:
            if self._number + 1 == self._record.number:
                self._event_system.raise_event(self._record.event)
                self._record = None
        else:
            self.stop()
        self._number += 1

    def _get_record_if_not_exist(self):
        if self._record:
            return self._record

        if self._records.readable():
            line = self._records.readline()
            if line:
                record_serialized = json.loads(line)
                return EventRecord.deserialize(record_serialized)
        return None

