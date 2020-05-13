from abc import ABC, abstractmethod
from typing import Sequence, Iterable

from lft.consensus.messages.message import Message, MessagePool
from lft.consensus.messages.vote import Vote

__all__ = ("Data", "DataFactory", "DataPool", "DataVerifier")


class Data(Message):
    @property
    @abstractmethod
    def number(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def prev_id(self) -> bytes:
        raise NotImplementedError

    @property
    @abstractmethod
    def proposer_id(self) -> bytes:
        raise NotImplementedError

    @property
    @abstractmethod
    def prev_votes(self) -> Sequence['Vote']:
        raise NotImplementedError

    @abstractmethod
    def is_none(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def is_lazy(self) -> bool:
        raise NotImplementedError

    def is_real(self) -> bool:
        return not self.is_none() and not self.is_lazy()

    def is_determinative(self) -> bool:
        return not self.is_lazy()

    def is_genesis(self) -> bool:
        return self.epoch_num == 0 and self.round_num == 0

    def __eq__(self, other):
        return self.id == other.id \
               and self.number == other.number \
               and self.prev_id == other.prev_id \
               and self.proposer_id == other.proposer_id \
               and self.epoch_num == other.epoch_num \
               and self.round_num == other.round_num \
               and self.prev_votes == other.prev_votes

    def __hash__(self):
        return int.from_bytes(self.id, "big")


class DataVerifier(ABC):
    @abstractmethod
    async def verify(self, prev_data: 'Data', data: 'Data'):
        """Verify Data.
        
        :param prev_data:
        :param data:
        :raises:
            Exception:
        """
        raise NotImplementedError


class DataFactory(ABC):
    @abstractmethod
    async def create_data(self,
                          data_number: int,
                          prev_id: bytes,
                          epoch_num: int,
                          round_num: int,
                          prev_votes: Sequence['Vote']) -> 'Data':
        raise NotImplementedError

    @abstractmethod
    def create_none_data(self,
                         epoch_num: int,
                         round_num: int,
                         proposer_id: bytes) -> 'Data':
        raise NotImplementedError

    @abstractmethod
    def create_lazy_data(self,
                         epoch_num: int,
                         round_num: int,
                         proposer_id: bytes) -> 'Data':
        raise NotImplementedError

    @abstractmethod
    async def create_data_verifier(self) -> 'DataVerifier':
        raise NotImplementedError


class DataPool(MessagePool):
    def add_data(self, data: Data):
        if data.is_real():
            self.add_message(data)
        else:
            # To avoid id collision dummy_id is generated.
            # Unreal data must be added for node recovery and removed by only pruning
            dummy_id = self._int_to_bytes(data.epoch_num) + data.id + self._int_to_bytes(data.round_num)
            self._messages[dummy_id] = data

    def get_data(self, data_id: bytes) -> Data:
        # Only real data can be gotten.
        return self.get_message(data_id)

    def get_datums(self, epoch_num: int, round_num: int) -> Iterable[Data]:
        return self.get_messages(epoch_num, round_num)

    def get_datums_connected(self, prev_id: bytes) -> Iterable[Data]:
        for data in self._messages.values():
            if data.prev_id == prev_id:
                yield data

    def prune_data(self, latest_epoch_num: int, latest_round_num: int):
        super().prune_message(latest_epoch_num, latest_round_num)

    def _int_to_bytes(self, x: int) -> bytes:
        return x.to_bytes((x.bit_length() + 7) // 8, 'big')
