import asyncio
import traceback
from collections import defaultdict
from typing import DefaultDict, Type, List, Callable, Coroutine, Any, Union, Optional

HandlerCoroutine = Callable[[Any], Coroutine]
HandlerFunc = Callable[[Any], None],
HandlerCallable = Union['HandlerFunc', 'HandlerCoroutine']


class EventSystem:
    def __init__(self):
        self._events = asyncio.Queue()
        self._opened = True
        self._handlers: DefaultDict[Type, List[HandlerCoroutine]] = defaultdict(list)

    def __del__(self):
        self.close()

    def register_handler(self, event_type: Type, handler: HandlerCallable):
        handler = asyncio.coroutine(handler)
        self._handlers[event_type].append(handler)
        return handler

    def unregister_handler(self, event_type: Type, handler: HandlerCoroutine):
        self._handlers[event_type].remove(handler)

    def raise_event(self, event: Any):
        self._events.put_nowait(event)

    def close(self):
        self._opened = False
        self.raise_event(None)

    async def execute_events(self):
        while self._opened:
            event = await self._events.get()
            if not event:
                break
            await self._execute_event(event)

    async def _execute_event(self, event):
        for handler in self._handlers[type(event)]:
            try:
                await handler(event)
            except Exception:
                traceback.print_exc()

    def run_forever(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        loop = loop or asyncio.get_event_loop()
        loop.run_until_complete(self.execute_events())
