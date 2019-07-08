import json
import time
import os
from collections import deque
from typing import IO
from lft.event import EventMediator, EventInstantMediatorExecutor, EventRecorder, EventReplayer
from lft.event import EventReplayerMediatorExecutor, EventRecorderMediatorExecutor


class TimestampEventInstantMediatorExecutor(EventInstantMediatorExecutor):
    def execute(self):
        return int(time.time() * 1_000_000)

    async def execute_async(self):
        return super().execute()


class TimestampEventRecorderMediatorExecutor(EventRecorderMediatorExecutor):
    def __init__(self, event_recorder: EventRecorder, io: IO):
        super().__init__(event_recorder)
        self._io = io

    def execute(self):
        result = None
        try:
            result = int(time.time() * 1_000_000)
        except Exception as e:
            result = e
            raise e
        else:
            return result
        finally:
            self._write(result)

    async def execute_async(self):
        return super().execute()

    def _write(self, result):
        number = self._event_recorder.number
        serialized = serialize(number, result)
        dumped = json.dumps(serialized)

        self._io.write(dumped)
        self._io.write(os.linesep)


class TimestampEventReplayerMediatorExecutor(EventReplayerMediatorExecutor):
    def __init__(self, event_replayer: EventReplayer, io: IO):
        super().__init__(event_replayer)
        self._io = io

    def execute(self):
        last_number = None
        last_result = None

        while self._is_less_last_number(last_number):
            last_number, last_result = self._read()

        if not self._is_equal_last_number(last_number):
            raise RuntimeError

        if isinstance(last_result, Exception):
            raise last_result
        else:
            return last_result

    async def execute_async(self):
        return self.execute()

    def _read(self):
        dumped = self._io.readline()
        if not dumped:
            return None, None
        if dumped == os.linesep:
            return None, None
        serialized = json.loads(dumped)
        return deserialize(serialized)

    def _is_less_last_number(self, last_number: int):
        return (
            last_number is None or
            last_number < self._event_replayer.number
        )

    def _is_equal_last_number(self, last_number: int):
        return (
            last_number is not None and
            last_number == self._event_replayer.number
        )


class TimestampEventMediator(EventMediator):
    InstantExecutorType = TimestampEventInstantMediatorExecutor
    RecorderExecutorType = TimestampEventRecorderMediatorExecutor
    ReplayerExecutorType = TimestampEventReplayerMediatorExecutor

    def execute(self):
        return super().execute()


def serialize(number: int, timestamp: int) -> dict:
    return {
        "number": number,
        "timestamp": timestamp
    }


def deserialize(serialized: dict) -> (int, int):
    return serialized["number"], serialized["timestamp"]
