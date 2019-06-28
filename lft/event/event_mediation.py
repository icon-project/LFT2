import traceback
from abc import ABC, abstractmethod
from typing import Optional, Type
from lft.event import EventSimulator, EventRecorder, EventReplayer


class EventMediationExecutor(ABC):
    @abstractmethod
    def execute(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def execute_async(self, **kwargs):
        raise NotImplementedError


class EventInstantMediationExecutor(EventMediationExecutor):
    def __init__(self, event_simulator: EventSimulator):
        self._event_simulator = event_simulator


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

    def switch_instant(self, event_system: EventSimulator, **kwargs):
        self._executor = self.InstantExecutorType(event_system, **kwargs)

    def switch_recorder(self, event_recorder: EventRecorder, **kwargs):
        self._executor = self.RecorderExecutorType(event_recorder, **kwargs)

    def switch_replayer(self, event_replayer: EventReplayer, **kwargs):
        self._executor = self.ReplayerExecutorType(event_replayer, **kwargs)

    def execute(self, **kwargs):
        return self._executor.execute(**kwargs)

    async def execute_async(self, **kwargs):
        return await self._executor.execute_async(**kwargs)
