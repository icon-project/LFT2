from io import StringIO
from typing import Type, TypeVar
from lft.event import EventSystem, EventRecorder, EventReplayer, Event, SerializableEvent
from lft.event.mediation import DelayedEventMediation

T = TypeVar("T")


class Event1(SerializableEvent):
    def serialize(self) -> str:
        return ""

    @classmethod
    def deserialize(cls: Type[T], event_serialized: str) -> T:
        return Event1()


class Event2(Event):
    pass


class Event3(SerializableEvent):
    def __init__(self, num: int):
        self.num = num

    def serialize(self) -> str:
        return str(self.num)

    @classmethod
    def deserialize(cls: Type[T], event_serialized: str) -> T:
        return Event3(int(event_serialized))


def on_test1(event1: Event1, results: list, event_system: EventSystem):
    print("on_test1")
    results.append(1)
    event_system.raise_event(Event2())


def on_test2(event2: Event2, results: list, delayed_event_mediation: DelayedEventMediation):
    print("on_test2")
    results.append(2)

    event3 = Event3(3)
    event3.deterministic = False
    delayed_event_mediation.execute(3, event3)


def on_test3(event3: Event3, results: list, event_system: EventSystem):
    print("on_test3")
    results.append(3)
    event_system.stop()


def test_event_system():
    results = []

    event_system = EventSystem()
    record_io = StringIO()
    recorder = EventRecorder(event_system, record_io)

    delayed_event_mediation = DelayedEventMediation()
    delayed_event_mediation.switch_recorder(recorder)
    event_system.register_handler(Event1, lambda e: on_test1(e, results, event_system))
    event_system.register_handler(Event2, lambda e: on_test2(e, results, delayed_event_mediation))
    event_system.register_handler(Event3, lambda e: on_test3(e, results, event_system))

    event = Event1()
    event.deterministic = False
    event_system.raise_event(event)

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
    delayed_event_mediation.switch_replayer(replayer)
    event_system.start()

    assert original_results == results
