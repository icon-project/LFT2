import asyncio
from lft.event import Event, SerializableEvent
from lft.event import EventMediation, EventInstantMediationExecutor
from lft.event import EventReplayerMediationExecutor, EventRecorderMediationExecutor


class DelayedEventInstantMediationExecutor(EventInstantMediationExecutor):
    def execute(self, delay: float, event: Event, loop: asyncio.AbstractEventLoop=None):
        _is_valid_event(event)

        loop = loop or asyncio.get_event_loop()
        loop.call_later(delay, lambda: self._event_system.raise_event(event))


class DelayedEventRecorderMediationExecutor(EventRecorderMediationExecutor):
    def execute(self, delay: float, event: Event, loop: asyncio.AbstractEventLoop=None):
        _is_valid_event(event)

        loop = loop or asyncio.get_event_loop()
        loop.call_later(delay, lambda: self._event_recorder.event_system.raise_event(event))


class DelayedEventReplayerMediationExecutor(EventReplayerMediationExecutor):
    def execute(self, delay: float, event: Event, loop: asyncio.AbstractEventLoop=None):
        # do nothing
        _is_valid_event(event)


class DelayedEventMediation(EventMediation):
    InstantExecutorType = DelayedEventInstantMediationExecutor
    RecorderExecutorType = DelayedEventRecorderMediationExecutor
    ReplayerExecutorType = DelayedEventReplayerMediationExecutor

    def execute(self, delay: float, event: Event, loop: asyncio.AbstractEventLoop=None):
        return super().execute(delay=delay, event=event, loop=loop)


def _is_valid_event(event: Event):
    if event.deterministic:
        raise RuntimeError("Delayed event must not be deterministic")
    if not isinstance(event, SerializableEvent):
        raise RuntimeError("Delayed event must be serializable")

