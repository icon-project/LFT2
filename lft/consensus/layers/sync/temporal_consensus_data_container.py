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
""" Contains consensus data that has number over than criteria"""
from collections import defaultdict
from typing import Dict

from lft.consensus.data import Data


class TemporalDataContainer:
    def __init__(self, criteria: int):
        self._criteria = criteria
        self._datums: Dict[int, Dict[bytes, 'Data']] = defaultdict(dict)

    def add_data(self, data: Data):
        if data.number < self._criteria:
            return
        self._datums[data.number][data.id] = data

    def get_data(self, number: int, id_: bytes) -> Data:
        return self._datums[number][id_]

    def update_criteria(self, criteria: int):
        self._criteria = criteria
        past_numbers = []
        for number in self._datums.keys():
            if self._criteria < number:
                past_numbers.append(number)
        for number in past_numbers:
            del self._datums[number]
