from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from lft.event import EventSystem


class Blockchain:
    def __init__(self, event_system: 'EventSystem'):
        self._event_system = event_system

