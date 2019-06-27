import time
import os
from collections import deque
from typing import IO
from lft.event import EventMediation, EventInstantMediationExecutor, EventRecorder, EventReplayer
from lft.event import EventReplayerMediationExecutor, EventRecorderMediationExecutor


class TimestampEventInstantMediationExecutor(EventInstantMediationExecutor):
    def execute(self):
        return int(time.time() * 1_000_000)


class TimestampEventRecorderMediationExecutor(EventRecorderMediationExecutor):
    def __init__(self, event_recorder: EventRecorder, io: IO):
        super().__init__(event_recorder)
        self._io = io
        self._number = -1
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


class TimestampEventReplayerMediationExecutor(EventReplayerMediationExecutor):
    def __init__(self, event_replayer: EventReplayer, io: IO):
        super().__init__(event_replayer)
        self._io = io
        self._number = -1
        self._timestamps = None

    def execute(self):
        if self._number != self._event_replayer.number:
            line = self._io.readline()
            number, timestamps = line.split(":")
            self._number = int(number)
            self._timestamps = deque(int(timestamp) for timestamp in timestamps.split(",") if timestamp.isdecimal())
        return self._timestamps.popleft()


class TimestampEventMediation(EventMediation):
    InstantExecutorType = TimestampEventInstantMediationExecutor
    RecorderExecutorType = TimestampEventRecorderMediationExecutor
    ReplayerExecutorType = TimestampEventReplayerMediationExecutor

    def execute(self):
        return super().execute()
