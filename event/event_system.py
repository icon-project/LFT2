import asyncio
import types
from collections import defaultdict
from typing import DefaultDict, Type, List, Callable, Coroutine, Any, Union


class EventSystem:
    def __init__(self):
        self._events = []
        self._event_waiter = asyncio.Event()

        self._handlers: DefaultDict[Type, List[Callable[[Any], Coroutine]]] = defaultdict(list)
        self._receivers: List[Callable[[List[Any]], Coroutine]] = []

    def register_handler(self, event_type: Type, handler: Union[Callable[[Any], None], Callable[[Any], Coroutine]]):
        coroutine = types.coroutine(handler)
        self._handlers[event_type].append(coroutine)

    def register_receiver(self, receiver: Union[Callable[[List[Any]], None], Callable[[List[Any]], Coroutine]]):
        coroutine = types.coroutine(receiver)
        self._receivers.append(coroutine)

    def raise_event(self, event: Any):
        self._events.append(event)
        self._event_waiter.set()

    def flush_events(self):
        events = self._events
        self._events = []
        return events

    async def execute_events(self):
        await self._event_waiter.wait()
        try:
            events = self.flush_events()
        finally:
            self._event_waiter.clear()

        for event in events:
            for handler in self._handlers[type(event)]:
                await handler(event)
        for receiver in self._receivers:
            await receiver(events)

    async def run_forever(self):
        while True:
            await self.execute_events()
