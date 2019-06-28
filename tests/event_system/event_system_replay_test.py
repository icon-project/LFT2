from io import StringIO
from typing import Type, TypeVar
from lft.event import EventSystem, EventRecorder, EventReplayer, Event, SerializableEvent
from lft.event.mediations import DelayedEventMediation, TimestampEventMediation, JsonRpcEventMediation

T = TypeVar("T")


def test_event_system():
    results = []

    event_system = EventSystem()
    record_io = StringIO()
    recorder = EventRecorder(event_system, record_io)

    delayed_event_mediation = DelayedEventMediation()
    delayed_event_mediation.switch_recorder(recorder)

    timestamp_io = StringIO()
    timestamp_event_mediation = TimestampEventMediation()
    timestamp_event_mediation.switch_recorder(recorder, io=timestamp_io)

    http_io = StringIO()
    json_rpc_event_mediation = JsonRpcEventMediation()
    json_rpc_event_mediation.switch_recorder(recorder, io=http_io)

    event_system.register_handler(Event1, lambda e: on_test1(e, results, event_system, timestamp_event_mediation, json_rpc_event_mediation))
    event_system.register_handler(Event2, lambda e: on_test2(e, results, timestamp_event_mediation, delayed_event_mediation, json_rpc_event_mediation))
    event_system.register_handler(Event3, lambda e: on_test3(e, results, event_system, timestamp_event_mediation, json_rpc_event_mediation))

    event = Event1()
    event.deterministic = False
    event_system.raise_event(event)

    recorder.start()
    event_system.start()
    recorder.stop()
    event_system.clear()
    # stopped #

    record_io.seek(0)
    record_str = record_io.read()
    record_io.close()

    timestamp_io.seek(0)
    timestamp_str = timestamp_io.read()
    timestamp_io.close()

    http_io.seek(0)
    http_str = http_io.read()
    http_io.close()

    record_io = StringIO()
    record_io.write(record_str)
    record_io.seek(0)

    timestamp_io = StringIO()
    timestamp_io.write(timestamp_str)
    timestamp_io.seek(0)

    http_io = StringIO()
    http_io.write(http_str)
    http_io.seek(0)

    original_results = list(results)
    results.clear()

    replayer = EventReplayer(event_system)
    replayer.start(record_io)
    delayed_event_mediation.switch_replayer(replayer)
    timestamp_event_mediation.switch_replayer(replayer, io=timestamp_io)
    json_rpc_event_mediation.switch_replayer(replayer, io=http_io)
    event_system.start()

    print(original_results)
    print(results)

    assert all(type(result0) == type(result1) if isinstance(result0, Exception) else result0 == result1
               for result0, result1 in zip(original_results, results))


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


def on_test1(event1: Event1, results: list, event_system: EventSystem, timestamp_mediation: TimestampEventMediation, json_rpc_mediation: JsonRpcEventMediation):
    print("on_test1")

    timestamp = timestamp_mediation.execute()
    results.append(timestamp)

    timestamp = timestamp_mediation.execute()
    results.append(timestamp)

    try:
        json_rpc_mediation.execute("https://wallet.icon.foundation/api/v3", "icx_getLastBlock1")
    except Exception as e:
        results.append(e)

    try:
        json_rpc_mediation.execute("https://wallet.icon.foundation1l/api/v3", "icx_getLastBlock")
    except Exception as e:
        results.append(e)

    event_system.raise_event(Event2())


def on_test2(event2: Event2, results: list, timestamp_mediation: TimestampEventMediation, delayed_mediation: DelayedEventMediation, json_rpc_mediation: JsonRpcEventMediation):
    print("on_test2")

    timestamp = timestamp_mediation.execute()
    results.append(timestamp)

    response = json_rpc_mediation.execute("https://wallet.icon.foundation/api/v3", "icx_getLastBlock")
    results.append(response.text)

    event3 = Event3(3)
    event3.deterministic = False
    delayed_mediation.execute(10, event3)


def on_test3(event3: Event3, results: list, event_system: EventSystem, timestamp_mediation: TimestampEventMediation, json_rpc_mediation: JsonRpcEventMediation):
    print("on_test3")

    timestamp = timestamp_mediation.execute()
    results.append(timestamp)

    response = json_rpc_mediation.execute("https://wallet.icon.foundation/api/v3", "icx_getLastBlock")
    results.append(response.text)

    event_system.stop()

