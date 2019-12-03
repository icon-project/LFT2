import asyncio
from typing import Set, Optional
from lft.event import (Event, EventSimulator, EventMediator,
                       EventInstantMediatorExecutor, EventReplayerMediatorExecutor, EventRecorderMediatorExecutor)

__all__ = ("DelayedHandlerMixin", "DelayedEventMediator", "DelayedHandler", "DelayedEventInstantMediatorExecutor",
           "DelayedEventRecorderMediatorExecutor", "DelayedEventReplayerMediatorExecutor")


class DelayedHandlerMixin:
    def __init__(self):
        self.handlers: Set['DelayedHandler'] = set()

    def _handle(self,
                loop: asyncio.AbstractEventLoop,
                delay: float,
                event: Event,
                event_simulator: EventSimulator):
        delayed_handler = DelayedHandler()
        self.handlers.add(delayed_handler)

        loop = loop or asyncio.get_event_loop()
        timer_handler = loop.call_later(delay, delayed_handler)

        delayed_handler.event = event
        delayed_handler.event_simulator = event_simulator
        delayed_handler.timer_handler = timer_handler
        delayed_handler.handlers = self.handlers


class DelayedEventInstantMediatorExecutor(EventInstantMediatorExecutor, DelayedHandlerMixin):
    def execute(self, delay: float, event: Event, loop: asyncio.AbstractEventLoop=None):
        _is_valid_event(event)
        self._handle(loop, delay, event, self._event_simulator)

    async def execute_async(self, delay: float, event: Event, loop: asyncio.AbstractEventLoop=None):
        return self.execute(delay, event, loop)


class DelayedEventRecorderMediatorExecutor(EventRecorderMediatorExecutor, DelayedHandlerMixin):
    def execute(self, delay: float, event: Event, loop: asyncio.AbstractEventLoop=None):
        _is_valid_event(event)
        self._handle(loop, delay, event, self._event_recorder.event_simulator)

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


class DelayedHandler:
    def __init__(self):
        self.event: Optional[Event] = None
        self.event_simulator: Optional[EventSimulator] = None
        self.timer_handler: Optional[asyncio.TimerHandle] = None
        self.handlers: Optional[Set['DelayedHandler']] = None

    def __call__(self):
        self.handlers.remove(self)
        self.event_simulator.raise_event(self.event)

