import os
from typing import IO
from lft.event import EventSimulator, EventRecord, Event, AnyEvent
from lft.serialization import Serializer


__all__ = ("EventReplayer", )


class EventReplayer:
    INIT_EVENT_COUNT = 1

    def __init__(self, event_simulator: EventSimulator):
        self.event_simulator = event_simulator
        self.number = -self.INIT_EVENT_COUNT  # EventReplayer raises a trash event(AnyEvent) first to start event system

        self._serializer = Serializer()
        self._record: EventRecord = None
        self._records: IO = None
        self._handler = None

    def __del__(self):
        self.close()

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
        while True:
            self._record = self._get_record_if_not_exist()
            if self._record and self._record.number <= self.number + 1:
                self.event_simulator.raise_event(self._record.event)
                self._record = None
            else:
                break

        self.number += 1

    def _get_record_if_not_exist(self):
        if self._record:
            return self._record

        while self._records.readable():
            line = self._records.readline()
            if not line:
                return None
            elif line == os.linesep:
                continue
            else:
                return self._serializer.deserialize(line)

