from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from lft.event import EventSimulator


class Blockchain:
    def __init__(self, event_system: 'EventSimulator'):
        self._event_system = event_system

