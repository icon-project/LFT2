import asyncio
import logging
import time
import traceback
from collections import defaultdict
from typing import DefaultDict, Type, TypeVar, List, Callable, Awaitable, Union, Optional
from lft.event import Event, AnyEvent

__all__ = ("EventSimulator", "TEvent", "HandlerAwaitable", "HandlerFunction", "HandlerCallable")

TEvent = TypeVar("TEvent", bound=Event)

HandlerAwaitable = Callable[[TEvent], Awaitable]
HandlerFunction = Callable[[TEvent], None]
HandlerCallable = Union[HandlerFunction, HandlerAwaitable]


class EventSimulator:
    def __init__(self, logger: Optional[logging.Logger] = None, use_priority=True):
        self._event_tasks = asyncio.PriorityQueue() if use_priority else asyncio.Queue()
        self._running = False
        self._handlers: DefaultDict[Type[TEvent], List[HandlerAwaitable]] = defaultdict(list)

        if logger is None:
            logger = logging.getLogger(__name__)
        self._logger = logger

    def __del__(self):
        self.stop()

    def register_handler(self, event_type: Type[TEvent], handler: HandlerCallable):
        handler = asyncio.coroutine(handler)
        self._handlers[event_type].append(handler)
        return handler

    def unregister_handler(self, event_type: Type[TEvent], handler: HandlerAwaitable):
        self._handlers[event_type].remove(handler)

    def raise_event(self, event: Event):
        event_task = (not event.deterministic, time.perf_counter(), event)
        self._event_tasks.put_nowait(event_task)

    async def execute_events(self):
        while self._running:
            try:
                event_task = await self._event_tasks.get()
            except RuntimeError:
                break

            non_deterministic, mono_ns, event = event_task
            if not event:
                break
            if not self._running:
                self._event_tasks.put_nowait(event_task)
                break

            await self._execute_event(event)

    async def _execute_event(self, event: Event):
        if not isinstance(event, AnyEvent):
            self._logger.debug(event)
        if type(event) is AnyEvent:
            handlers = self._handlers[AnyEvent][:]
        else:
            handlers = self._handlers[AnyEvent] + self._handlers[type(event)]

        for handler in handlers:
            try:
                await handler(event)
            except Exception:
                traceback.print_exc()

    def start(self, blocking=True, loop: Optional[asyncio.AbstractEventLoop] = None) -> Optional[asyncio.Task]:
        self._running = True

        loop = loop or asyncio.get_event_loop()
        if blocking:
            return loop.run_until_complete(self.execute_events())
        else:
            return loop.create_task(self.execute_events())

    def stop(self):
        self._running = False

    def clear(self):
        self._event_tasks = self._event_tasks.__class__()
        self._running = False
