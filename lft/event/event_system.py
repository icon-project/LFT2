import asyncio
import traceback
from collections import defaultdict
from typing import DefaultDict, Type, List, Callable, Coroutine, Union, Optional
from lft.event import Event, AnyEvent

HandlerCoroutine = Callable[[Event], Coroutine]
HandlerFunc = Callable[[Event], None],
HandlerCallable = Union['HandlerFunc', 'HandlerCoroutine']


class EventSystem:
    def __init__(self):
        self._events = asyncio.Queue()
        self._running = False
        self._handlers: DefaultDict[Type, List[HandlerCoroutine]] = defaultdict(list)

    def __del__(self):
        self.stop()

    def register_handler(self, event_type: Type, handler: HandlerCallable):
        handler = asyncio.coroutine(handler)
        self._handlers[event_type].append(handler)
        return handler

    def unregister_handler(self, event_type: Type, handler: HandlerCoroutine):
        self._handlers[event_type].remove(handler)

    def raise_event(self, event: Event):
        self._events.put_nowait(event)

    async def execute_events(self):
        while self._running:
            event = await self._events.get()
            if not event:
                break
            await self._execute_event(event)

    async def _execute_event(self, event: Event):
        if type(event) is AnyEvent:
            handlers = self._handlers[AnyEvent]
        else:
            handlers = self._handlers[AnyEvent] + self._handlers[type(event)]

        for handler in handlers:
            try:
                await handler(event)
            except Exception:
                traceback.print_exc()

    def start(self, blocking=True, loop: Optional[asyncio.AbstractEventLoop] = None):
        self._running = True

        loop = loop or asyncio.get_event_loop()
        if blocking:
            loop.run_until_complete(self.execute_events())
        else:
            loop.create_task(self.execute_events())

    def stop(self):
        self._running = False
        self.raise_event(None)

    def clear(self):
        self._events = asyncio.Queue()
        self._running = False
