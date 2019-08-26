# -*- coding: utf-8 -*-

# Copyright 2019 ICON Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from typing import Callable, Type

from lft.event import EventSystem
from lft.event.event_simulator import TEvent


class EventHandlerManager:
    def __init__(self, event_system: EventSystem):
        self._event_system = event_system
        self._handlers = {}

    def __del__(self):
        self.close()

    def close(self):
        for event_type, handler in self._handlers.items():
            self._event_system.simulator.unregister_handler(event_type, handler)
        self._handlers.clear()

    def _add_handler(self, event: Type[TEvent], handler: Callable):
        self._handlers[event] = self._event_system.simulator.register_handler(event, handler)
