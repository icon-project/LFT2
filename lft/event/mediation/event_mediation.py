import traceback
from abc import ABC, abstractmethod
from typing import Optional, Type
from lft.event import EventSystem, EventRecorder, EventReplayer


class EventMediationExecutor(ABC):
    @abstractmethod
    def execute(self, **kwargs):
        raise NotImplementedError


class EventInstantMediationExecutor(EventMediationExecutor):
    def __init__(self, event_system: EventSystem):
        self._event_system = event_system


class EventRecorderMediationExecutor(EventMediationExecutor):
    def __init__(self, event_recorder: EventRecorder):
        self._event_recorder = event_recorder


class EventReplayerMediationExecutor(EventMediationExecutor):
    def __init__(self, event_replayer: EventReplayer):
        self._event_replayer = event_replayer


class EventMediation:
    InstantExecutorType: Type[EventInstantMediationExecutor]
    RecorderExecutorType: Type[EventRecorderMediationExecutor]
    ReplayerExecutorType: Type[EventReplayerMediationExecutor]

    def __init__(self):
        self._executor: Optional[EventMediationExecutor] = None

    def switch_instant(self, event_system: EventSystem):
        self._executor = self.InstantExecutorType(event_system)

    def switch_recorder(self, event_recorder: EventRecorder):
        self._executor = self.RecorderExecutorType(event_recorder)

    def switch_replayer(self, event_replayer: EventReplayer):
        self._executor = self.ReplayerExecutorType(event_replayer)

    def execute(self, **kwargs):
        try:
            return self._executor.execute(**kwargs)
        except Exception:
            traceback.print_exc()
