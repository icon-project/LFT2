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
from functools import partial
from typing import Type, Dict
from lft.event import EventSimulator
from lft.event.event_simulator import TEvent, HandlerCallable, HandlerAwaitable

__all__ = ("EventRegister", )


class EventRegister:
    _handler_prototypes: Dict[Type[TEvent], HandlerCallable] = {}

    def __init__(self, event_simulator: EventSimulator):
        self._event_simulator = event_simulator
        self._handlers: Dict[Type[TEvent], HandlerAwaitable] = {}
        self._register_handlers()

    def __del__(self):
        self.close()

    def close(self):
        self._unregister_handlers()

    def _register_handler(self, event_type: Type[TEvent]):
        handler = partial(self._handler_prototypes[event_type], self)
        self._handlers[event_type] = self._event_simulator.register_handler(event_type, handler)

    def _register_handlers(self):
        for event_type in self._handler_prototypes:
            self._register_handler(event_type)

    def _unregister_handler(self, event_type: Type[TEvent]):
        handler = self._handlers.pop(event_type)
        self._event_simulator.unregister_handler(event_type, handler)

    def _unregister_handlers(self):
        for event_type, handler in self._handlers.items():
            self._event_simulator.unregister_handler(event_type, handler)
        self._handlers.clear()
