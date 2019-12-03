from abc import ABCMeta
from typing import Type, TypeVar

__all__ = ("SerializableMeta", "Serializable")

T = TypeVar("T")


def get_type_name(cls: type):
    return f"{cls.__module__}.{cls.__qualname__}"


class SerializableMeta(ABCMeta):
    types = {}

    def __init__(cls, cls_name, bases, attrs):
        super().__init__(cls_name, bases, attrs)
        cls.types[get_type_name(cls)] = cls


class Serializable(metaclass=SerializableMeta):
    def serialize(self) -> dict:
        return {
            "!type": get_type_name(self.__class__),
            "!data": self._serialize()
        }

    def _serialize(self) -> dict:
        return self.__dict__

    @classmethod
    def deserialize(cls: Type[T], serialized: dict) -> T:
        type_name = serialized["!type"]
        type_ = cls.types[type_name]

        data = serialized["!data"]
        return type_._deserialize(**data)

    @classmethod
    def _deserialize(cls: Type[T], **kwargs) -> T:
        return cls(**kwargs)

