import asyncio
from lft.event import Event
from lft.event import EventMediator, EventInstantMediatorExecutor
from lft.event import EventReplayerMediatorExecutor, EventRecorderMediatorExecutor


class DelayedEventInstantMediatorExecutor(EventInstantMediatorExecutor):
    def execute(self, delay: float, event: Event, loop: asyncio.AbstractEventLoop=None):
        print(f"executed event {event}")
        _is_valid_event(event)

        loop = loop or asyncio.get_event_loop()
        loop.call_later(delay, lambda: self._event_simulator.raise_event(event))

    async def execute_async(self, delay: float, event: Event, loop: asyncio.AbstractEventLoop=None):
        return self.execute(delay, event, loop)


class DelayedEventRecorderMediatorExecutor(EventRecorderMediatorExecutor):
    def execute(self, delay: float, event: Event, loop: asyncio.AbstractEventLoop=None):
        _is_valid_event(event)

        loop = loop or asyncio.get_event_loop()
        loop.call_later(delay, lambda: self._event_recorder.event_simulator.raise_event(event))

    async def execute_async(self, delay: float, event: Event, loop: asyncio.AbstractEventLoop=None):
        return self.execute(delay, event, loop)


class DelayedEventReplayerMediatorExecutor(EventReplayerMediatorExecutor):
    def execute(self, delay: float, event: Event, loop: asyncio.AbstractEventLoop=None):
        # do nothing
        _is_valid_event(event)

    async def execute_async(self, delay: float, event: Event, loop: asyncio.AbstractEventLoop=None):
        return self.execute(delay, event, loop)


class DelayedEventMediator(EventMediator):
    InstantExecutorType = DelayedEventInstantMediatorExecutor
    RecorderExecutorType = DelayedEventRecorderMediatorExecutor
    ReplayerExecutorType = DelayedEventReplayerMediatorExecutor

    def execute(self, delay: float, event: Event, loop: asyncio.AbstractEventLoop=None):
        return super().execute(delay=delay, event=event, loop=loop)


def _is_valid_event(event: Event):
    if event.deterministic:
        raise RuntimeError(f"Delayed event must not be deterministic :{event.serialize()}")
