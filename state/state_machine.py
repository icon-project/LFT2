import asyncio
from collections import defaultdict
from typing import Any, List, Dict, DefaultDict, Callable, Union, Coroutine, Type, TypeVar, Optional, TYPE_CHECKING
from state import Transition

if TYPE_CHECKING:
    from state import State


T = TypeVar("T")


class StateMachine:
    def __init__(self):
        self.state = ""

        self._states: Dict[str, 'State'] = {}
        self._transitions: DefaultDict[str, Dict[str, 'Transition']] = defaultdict(dict)

    def add_state(self, state_name: str, state: 'State'):
        assert state_name not in self._states
        self._states[state_name] = state

    def add_transition(self, from_name, to_name,
                       event_type: Type[T],
                       event_handler: Optional[Union[Callable[[T], bool], Callable[[T], Coroutine]]] = lambda _: True):
        try:
            transition = self._transitions[from_name][to_name]
        except KeyError:
            transition = Transition()
            self._transitions[from_name][to_name] = transition
        transition.event_handlers[event_type] = asyncio.coroutine(event_handler)

    async def transfer_states(self, events: List[Any]):
        for event in events:
            from_name = self.state
            for to_name in self._transitions[from_name]:
                transition = self._transitions[from_name][to_name]
                if await self._transfer_state(event, transition, from_name, to_name):
                    break

    async def _transfer_state(self, event: Any, transition: 'Transition', from_name: str, to_name: str):
        is_transferred = await transition.handle_event(event)
        if not is_transferred:
            return False

        from_state = self._states[from_name]
        await from_state.on_exit(event)

        self.state = to_name

        to_state = self._states[to_name]
        await to_state.on_enter(event)
        return True


