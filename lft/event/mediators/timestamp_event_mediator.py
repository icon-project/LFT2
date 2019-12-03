import time
from typing import IO
from lft.event import EventMediator, EventInstantMediatorExecutor, EventRecorder, EventReplayer
from lft.event import EventReplayerMediatorExecutor, EventRecorderMediatorExecutor
from lft.event.mediators.mixin import EventMediatorRecorderMixin

__all__ = ("TimestampEventMediator", "TimestampEventInstantMediatorExecutor",
           "TimestampEventRecorderMediatorExecutor", "TimestampEventReplayerMediatorExecutor")


class TimestampEventInstantMediatorExecutor(EventInstantMediatorExecutor):
    def execute(self):
        return int(time.time() * 1_000_000)

    async def execute_async(self):
        return super().execute()


class TimestampEventRecorderMediatorExecutor(EventRecorderMediatorExecutor, EventMediatorRecorderMixin):
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
            self._write(self._io, self._event_recorder.number, result)

    async def execute_async(self):
        return super().execute()


class TimestampEventReplayerMediatorExecutor(EventReplayerMediatorExecutor, EventMediatorRecorderMixin):
    def __init__(self, event_replayer: EventReplayer, io: IO):
        super().__init__(event_replayer)
        self._io = io

    def execute(self):
        return self._read(self._io, self._event_replayer.number)

    async def execute_async(self):
        return self.execute()


class TimestampEventMediator(EventMediator):
    InstantExecutorType = TimestampEventInstantMediatorExecutor
    RecorderExecutorType = TimestampEventRecorderMediatorExecutor
    ReplayerExecutorType = TimestampEventReplayerMediatorExecutor

    def execute(self):
        return super().execute()
