from abc import ABC, abstractmethod
from typing import Optional, Type
from lft.event import EventSimulator, EventRecorder, EventReplayer

__all__ = ("EventMediatorExecutor", "EventMediator",
           "EventInstantMediatorExecutor", "EventRecorderMediatorExecutor", "EventReplayerMediatorExecutor")


class EventMediatorExecutor(ABC):
    @abstractmethod
    def execute(self, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def execute_async(self, **kwargs):
        raise NotImplementedError


class EventInstantMediatorExecutor(EventMediatorExecutor):
    def __init__(self, event_simulator: EventSimulator):
        super().__init__()
        self._event_simulator = event_simulator


class EventRecorderMediatorExecutor(EventMediatorExecutor):
    def __init__(self, event_recorder: EventRecorder):
        super().__init__()
        self._event_recorder = event_recorder


class EventReplayerMediatorExecutor(EventMediatorExecutor):
    def __init__(self, event_replayer: EventReplayer):
        super().__init__()
        self._event_replayer = event_replayer


class EventMediator:
    InstantExecutorType: Type[EventInstantMediatorExecutor]
    RecorderExecutorType: Type[EventRecorderMediatorExecutor]
    ReplayerExecutorType: Type[EventReplayerMediatorExecutor]

    def __init__(self):
        self._executor: Optional[EventMediatorExecutor] = None

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
