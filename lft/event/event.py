from dataclasses import dataclass
from typing import Type, TypeVar

T = TypeVar("T")


def _get_type_name(cls: type):
    return f"{cls.__module__}.{cls.__qualname__}"


class EventMeta(type):
    types = {}

    def __init__(cls, cls_name, bases, attrs):
        super().__init__(cls_name, bases, attrs)
        cls.types[_get_type_name(cls)] = cls


@dataclass
class Event(metaclass=EventMeta):

    deterministic = True

    def serialize(self) -> dict:
        items = self.__dict__
        items.pop("deterministic", None)
        return {
            "event_name": _get_type_name(self.__class__),
            "event_contents": items
        }

    @classmethod
    def deserialize(cls: Type[T], event_serialized: dict) -> T:
        event_name = event_serialized["event_name"]
        event_type = cls.types[event_name]

        event_contents = event_serialized["event_contents"]
        return event_type(**event_contents)


@dataclass
class AnyEvent(Event):
    pass

