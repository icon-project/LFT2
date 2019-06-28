from io import StringIO
from typing import Type, TypeVar
from itertools import zip_longest
from lft.event import EventSystem, Event, SerializableEvent
from lft.event.mediators import DelayedEventMediator, TimestampEventMediator, JsonRpcEventMediator

T = TypeVar("T")


def test_event_system():
    results = []

    event_system = EventSystem()
    event_system.set_mediator(TimestampEventMediator)
    event_system.set_mediator(DelayedEventMediator)
    event_system.set_mediator(JsonRpcEventMediator)

    event_system.simulator.register_handler(Event1, lambda e: on_test1(e, results, event_system))
    event_system.simulator.register_handler(Event2, lambda e: on_test2(e, results, event_system))
    event_system.simulator.register_handler(Event3, lambda e: on_test3(e, results, event_system))

    event = Event1()
    event.deterministic = False
    event_system.simulator.raise_event(event)

    record_io = StringIO()
    timestamp_io = StringIO()
    json_rpc_io = StringIO()
    event_system.start_record(record_io, {TimestampEventMediator: timestamp_io, JsonRpcEventMediator: json_rpc_io})
    # stopped #

    original_results = list(results)
    results.clear()

    record_io.seek(0)
    timestamp_io.seek(0)
    json_rpc_io.seek(0)
    event_system.simulator.clear()
    event_system.start_replay(record_io, {TimestampEventMediator: timestamp_io, JsonRpcEventMediator: json_rpc_io})

    print(original_results)
    print(results)

    assert all(type(result0) == type(result1) if isinstance(result0, Exception) else result0 == result1
               for result0, result1 in zip_longest(original_results, results))


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

    timestamp_mediator = event_system.get_mediator(TimestampEventMediator)
    timestamp = timestamp_mediator.execute()
    results.append(timestamp)

    timestamp = timestamp_mediator.execute()
    results.append(timestamp)

    json_rpc_mediator = event_system.get_mediator(JsonRpcEventMediator)
    try:
        json_rpc_mediator.execute("https://wallet.icon.foundation/api/v3", "icx_getLastBlock1")
    except Exception as e:
        results.append(e)

    try:
        json_rpc_mediator.execute("https://wallet.icon.foundation1l/api/v3", "icx_getLastBlock")
    except Exception as e:
        results.append(e)

    event_system.simulator.raise_event(Event2())


def on_test2(event2: Event2, results: list, event_system: EventSystem):
    print("on_test2")

    timestamp_mediator = event_system.get_mediator(TimestampEventMediator)
    timestamp = timestamp_mediator.execute()
    results.append(timestamp)

    json_rpc_mediator = event_system.get_mediator(JsonRpcEventMediator)
    response = json_rpc_mediator.execute("https://wallet.icon.foundation/api/v3", "icx_getLastBlock")
    results.append(response.text)

    event3 = Event3(3)
    event3.deterministic = False

    delayed_mediator = event_system.get_mediator(DelayedEventMediator)
    delayed_mediator.execute(3, event3)


def on_test3(event3: Event3, results: list, event_system: EventSystem):
    print("on_test3")

    timestamp_mediator = event_system.get_mediator(TimestampEventMediator)
    timestamp = timestamp_mediator.execute()
    results.append(timestamp)

    json_rpc_mediator = event_system.get_mediator(JsonRpcEventMediator)
    response = json_rpc_mediator.execute("https://wallet.icon.foundation/api/v3", "icx_getLastBlock")
    results.append(response.text)

    event_system.stop()
