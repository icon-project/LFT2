import pytest
from io import StringIO
from itertools import zip_longest
from typing import TypeVar, List

from lft.event import EventSystem, Event

T = TypeVar("T")


@pytest.mark.parametrize("use_priority,final_results", [(True, [1, 2, 3]), (False, [1, 3])])
def test_event_system_priority(use_priority: bool, final_results: List[int]):
    results = []

    event_system = EventSystem(use_priority)

    event_system.simulator.register_handler(Event1, lambda e: on_test1(e, results, event_system))
    event_system.simulator.register_handler(Event2, lambda e: on_test2(e, results, event_system))
    event_system.simulator.register_handler(Event3, lambda e: on_test3(e, results, event_system))

    event = Event1()
    event.deterministic = False
    event_system.simulator.raise_event(event)

    record_io = StringIO()
    event_system.start_record(record_io)
    # stopped #

    original_results = list(results)
    results.clear()

    record_io.seek(0)

    event_system.simulator.clear()
    event_system.start_replay(record_io)

    print(original_results)
    print(results)

    assert all(type(result0) == type(result1) if isinstance(result0, Exception) else result0 == result1
               for result0, result1 in zip_longest(original_results, results))

    assert results == final_results


class Event1(Event):
    pass


class Event2(Event):
    pass


class Event3(Event):
    pass


def on_test1(event1: Event1, results: list, event_system: EventSystem):
    print("on_test1")
    results.append(1)

    event3 = Event3()
    event3.deterministic = False
    event_system.simulator.raise_event(event3)

    event_system.simulator.raise_event(Event2())


def on_test2(event2: Event2, results: list, event_system: EventSystem):
    print("on_test2")
    results.append(2)

    event_system.simulator.raise_event(Event3())


def on_test3(event3: Event3, results: list, event_system: EventSystem):
    results.append(3)

    event_system.stop()
