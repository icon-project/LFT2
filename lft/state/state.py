from abc import ABC, abstractmethod
from typing import Any


class State(ABC):
    @abstractmethod
    async def on_enter(self, event: Any):
        raise NotImplementedError

    @abstractmethod
    async def on_exit(self, event: Any):
        raise NotImplementedError
