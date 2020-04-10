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
from typing import Sequence, Dict

from lft.consensus.messages.data import Data, Vote
from lft.serialization import Serializable

__all__ = ("Epoch", "EpochPool")


class Epoch(Serializable):
    @property
    @abstractmethod
    def num(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def quorum_num(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def voters_num(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def voters(self) -> Sequence[bytes]:
        raise NotImplementedError

    def verify_data(self, data: Data):
        self.verify_proposer(data.proposer_id, data.round_num)
        for i, prev_vote in enumerate(data.prev_votes):
            self.verify_vote(prev_vote, i)

    def verify_vote(self, vote: Vote, vote_index: int = -1):
        if isinstance(vote, Vote):
            self.verify_voter(vote.voter_id, vote_index)

    @abstractmethod
    def verify_proposer(self, proposer_id: bytes, round_num: int):
        """

        :param proposer_id:
        :param round_num:
        :raises:
            InvalidProposer:
            InvalidEpoch:
            InvalidRound:
        """
        raise NotImplementedError

    @abstractmethod
    def verify_voter(self, voter: bytes, vote_index: int = -1):
        raise NotImplementedError

    @abstractmethod
    def get_proposer_id(self, round_num: int) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def get_voter_id(self, vote_index: int) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def get_voters_id(self) -> Sequence[bytes]:
        raise NotImplementedError

    @abstractmethod
    def __eq__(self, other):
        raise NotImplementedError


class EpochPool:
    def __init__(self):
        self._epochs: Dict[int, Epoch] = {}

    def add_epoch(self, epoch: Epoch):
        self._epochs[epoch.num] = epoch

    def get_epoch(self, epoch_num: int):
        return self._epochs[epoch_num]

    def prune_epoch(self, latest_epoch_num: int):
        self._epochs = {epoch_num: epoch for epoch_num, epoch in self._epochs.items()
                       if epoch.num >= latest_epoch_num}
