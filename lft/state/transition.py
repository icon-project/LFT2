from typing import Callable, Dict, Any, Coroutine


class Transition:
    def __init__(self):
        self.event_handlers: Dict[Any, Callable[[Any], Coroutine]] = {}

    async def handle_event(self, event: Any) -> bool:
        try:
            handler = self.event_handlers[type(event)]
        except KeyError:
            return False
        else:
            return await handler(event)
