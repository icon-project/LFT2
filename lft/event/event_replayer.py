import json
from typing import IO
from lft.event import EventSimulator, EventRecord, Event, AnyEvent


class EventReplayer:
    def __init__(self, event_simulator: EventSimulator):
        self.event_simulator = event_simulator
        self.number = -1  # EventReplayer raises a trash event first to start event system

        self._record: EventRecord = None
        self._records: IO = None
        self._handler = None

    def __del__(self):
        self.stop()

    def start(self, records: IO):
        self.stop()

        self._records = records
        self._handler = self.event_simulator.register_handler(AnyEvent, self.on_event_replay)
        self.event_simulator.raise_event(AnyEvent())

    def stop(self):
        if self._handler:
            self.event_simulator.unregister_handler(AnyEvent, self._handler)
            self._handler = None

    def close(self):
        self.stop()
        if self._records and not self._records.closed:
            self._records.close()

    def on_event_replay(self, event: Event):
        self._record = self._get_record_if_not_exist()
        if self._record:
            if self.number + 1 == self._record.number:
                self.event_simulator.raise_event(self._record.event)
                self._record = None
        else:
            self.stop()
        self.number += 1

    def _get_record_if_not_exist(self):
        if self._record:
            return self._record

        if self._records.readable():
            line = self._records.readline()
            if line:
                record_serialized = json.loads(line)
                return EventRecord.deserialize(record_serialized)
        return None

