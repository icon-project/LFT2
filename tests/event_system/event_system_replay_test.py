from io import StringIO
from typing import Type, TypeVar
from lft.event import EventSystem, EventRecorder, EventReplayer, Event, SerializableEvent

T = TypeVar("T")


class Event1(SerializableEvent):
    def serialize(self) -> str:
        return ""

    @classmethod
    def deserialize(cls: Type[T], event_serialized: str) -> T:
        return Event1()


class Event2(Event):
    pass


def on_test1(event1: Event1, results: list, event_system: EventSystem):
    results.append(1)
    event_system.raise_event(Event2())


def on_test2(event2: Event2, results: list, event_system: EventSystem):
    results.append(2)
    event_system.stop()


def test_event_system():
    results = []
    event_system = EventSystem()
    event_system.register_handler(Event1, lambda e: on_test1(e, results, event_system))
    event_system.register_handler(Event2, lambda e: on_test2(e, results, event_system))
    event = Event1()
    event.deterministic = False
    event_system.raise_event(event)

    record_io = StringIO()
    recorder = EventRecorder(event_system, record_io)
    recorder.start()

    event_system.start()
    recorder.stop()
    # stopped #

    record_io.seek(0)
    record_str = record_io.read()
    record_io.close()
    print("Event")
    print(record_str)

    record_io = StringIO()
    record_io.write(record_str)
    record_io.seek(0)

    original_results = list(results)
    results.clear()

    event_system.clear()
    replayer = EventReplayer(event_system)
    replayer.start(record_io)
    event_system.start()

    assert original_results == results
