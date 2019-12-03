from dataclasses import dataclass
from typing import TypeVar
from lft.serialization import Serializable

__all__ = ("Event", "AnyEvent")

T = TypeVar("T")


@dataclass
class Event(Serializable):
    deterministic = True

    def _serialize(self) -> dict:
        items = self.__dict__.copy()
        items.pop("deterministic", None)
        return items


@dataclass
class AnyEvent(Event):
    pass

