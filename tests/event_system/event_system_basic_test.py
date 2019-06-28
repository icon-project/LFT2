from lft.event import EventSimulator, Event


def test_event_system():
    event_system, results, _ = _create_event_system()
    event_system.raise_event(Event1())
    event_system.start()

    assert results == [1, 2, 3]


def test_event_system_unregister():
    event_system, results, handlers = _create_event_system()
    event_system.unregister_handler(Event1, handlers[0])
    event_system.unregister_handler(Event2, handlers[1])

    event_system.register_handler(Event1, lambda e: event_system.raise_event(Event3()))
    event_system.raise_event(Event1())
    event_system.start()

    assert results == [3]


class Event1(Event):
    value = 1


class Event2(Event):
    value = 2


class Event3(Event):
    value = 3


def on_event1(event: Event1, results: list, event_system: EventSimulator):
    results.append(event.value)
    event_system.raise_event(Event2())


def on_event2(event: Event2, results: list, event_system: EventSimulator):
    results.append(event.value)
    event_system.raise_event(Event3())


async def on_event3(event: Event3, results: list, event_system: EventSimulator):
    results.append(event.value)
    event_system.stop()


def _create_event_system():
    results = []
    handlers = []

    event_system = EventSimulator()
    handler = event_system.register_handler(Event1, lambda e: on_event1(e, results, event_system))
    handlers.append(handler)

    handler = event_system.register_handler(Event2, lambda e: on_event2(e, results, event_system))
    handlers.append(handler)

    handler = event_system.register_handler(Event3, lambda e: on_event3(e, results, event_system))
    handlers.append(handler)

    return event_system, results, handlers
