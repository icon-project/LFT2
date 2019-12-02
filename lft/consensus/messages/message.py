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
from abc import abstractmethod
from typing import Dict, Iterable

from lft.serialization import Serializable


class Message(Serializable):
    @property
    @abstractmethod
    def id(self) -> bytes:
        raise NotImplementedError

    @property
    @abstractmethod
    def term_num(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def round_num(self) -> int:
        raise NotImplementedError


class MessagePool:
    def __init__(self):
        self._messages: Dict[bytes, Message] = {}

    def add_message(self, message: Message):
        self._messages[message.id] = message

    def get_message(self, message_id: bytes) -> Message:
        return self._messages[message_id]

    def get_messages(self, term_num: int, round_num: int) -> Iterable[Message]:
        for message in self._messages.values():
            if message.term_num == term_num and message.round_num == round_num:
                yield message

    def prune_message(self, latest_term_num: int, latest_round_num: int):
        self._messages = {
            mid: message for mid, message in self._messages.items()
            if ((message.term_num > latest_term_num) or
                (message.term_num == latest_term_num and message.round_num >= latest_round_num))
        }
