from abc import ABC, abstractmethod
from typing import Generic, Type, TypeVar

T = TypeVar("T")


class Event(ABC):
    deterministic = True


class AnyEvent(Event):
    pass


class SerializableEventMeta(type(Event)):
    types = {}

    def __init__(cls, cls_name, bases, attrs):
        super().__init__(cls_name, bases, attrs)
        cls.types[cls_name] = cls


class SerializableEvent(Event, Generic[T], metaclass=SerializableEventMeta):
    @abstractmethod
    def serialize(self) -> str:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def deserialize(cls: Type[T], event_serialized: str) -> T:
        raise NotImplementedError
