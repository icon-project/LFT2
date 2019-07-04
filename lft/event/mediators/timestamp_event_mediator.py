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
        self._number = 0
        self._started = False

    def execute(self):
        timestamp = int(time.time() * 1_000_000)
        if self._number != self._event_recorder.number:
            self._number = self._event_recorder.number

            if self._started:
                self._io.write(os.linesep)
            self._io.write(str(self._number))
            self._io.write(":")
        self._io.write(str(timestamp))
        self._io.write(",")
        self._started = True
        return timestamp

    async def execute_async(self):
        return super().execute()


class TimestampEventReplayerMediatorExecutor(EventReplayerMediatorExecutor):
    def __init__(self, event_replayer: EventReplayer, io: IO):
        super().__init__(event_replayer)
        self._io = io
        self._number = 0
        self._timestamps = None

    def execute(self):
        if self._number != self._event_replayer.number:
            while True:
                line = self._io.readline()
                if line and line != os.linesep:
                    break
            number, timestamps = line.split(":")
            self._number = int(number)
            self._timestamps = deque(int(timestamp) for timestamp in timestamps.split(",") if timestamp.isdecimal())
        return self._timestamps.popleft()

    async def execute_async(self):
        return super().execute()


class TimestampEventMediator(EventMediator):
    InstantExecutorType = TimestampEventInstantMediatorExecutor
    RecorderExecutorType = TimestampEventRecorderMediatorExecutor
    ReplayerExecutorType = TimestampEventReplayerMediatorExecutor

    def execute(self):
        return super().execute()
