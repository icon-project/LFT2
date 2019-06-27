import traceback
from abc import ABC, abstractmethod
from typing import Optional, Type
from lft.event import EventSystem, EventRecorder, EventReplayer


class EventMediationExecutor(ABC):
    @abstractmethod
    def execute(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def execute_async(self, **kwargs):
        raise NotImplementedError


class EventInstantMediationExecutor(EventMediationExecutor):
    def __init__(self, event_system: EventSystem, **kwargs):
        self._event_system = event_system


class EventRecorderMediationExecutor(EventMediationExecutor):
    def __init__(self, event_recorder: EventRecorder, **kwargs):
        self._event_recorder = event_recorder


class EventReplayerMediationExecutor(EventMediationExecutor):
    def __init__(self, event_replayer: EventReplayer, **kwargs):
        self._event_replayer = event_replayer


class EventMediation:
    InstantExecutorType: Type[EventInstantMediationExecutor]
    RecorderExecutorType: Type[EventRecorderMediationExecutor]
    ReplayerExecutorType: Type[EventReplayerMediationExecutor]

    def __init__(self):
        self._executor: Optional[EventMediationExecutor] = None

    def switch_instant(self, event_system: EventSystem, **kwargs):
        self._executor = self.InstantExecutorType(event_system, **kwargs)

    def switch_recorder(self, event_recorder: EventRecorder, **kwargs):
        self._executor = self.RecorderExecutorType(event_recorder, **kwargs)

    def switch_replayer(self, event_replayer: EventReplayer, **kwargs):
        self._executor = self.ReplayerExecutorType(event_replayer, **kwargs)

    def execute(self, **kwargs):
        try:
            return self._executor.execute(**kwargs)
        except Exception:
            traceback.print_exc()


