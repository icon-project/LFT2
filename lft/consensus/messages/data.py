from abc import ABC, abstractmethod
from typing import Sequence

from lft.consensus.messages.message import Message
from lft.consensus.messages.vote import Vote


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
    def is_not(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def is_none(self) -> bool:
        raise NotImplementedError

    def __eq__(self, other):
        return self.id == other.id \
               and self.number == other.number \
               and self.prev_id == other.prev_id \
               and self.proposer_id == other.proposer_id \
               and self.term_num == other.term_num \
               and self.round_num == other.round_num \
               and self.prev_votes == other.prev_votes

    def __hash__(self):
        return int.from_bytes(self.id, "big")


class DataVerifier(ABC):
    @abstractmethod
    async def verify(self, data: 'Data'):
        raise NotImplementedError

    async def add_vote(self, vote: 'Vote'):
        raise NotImplementedError


class DataFactory(ABC):
    @abstractmethod
    async def create_data(self,
                          data_number: int,
                          prev_id: bytes,
                          term_num: int,
                          round_num: int,
                          prev_votes: Sequence['Vote']) -> 'Data':
        raise NotImplementedError

    @abstractmethod
    async def create_not_data(self,
                              term_num: int,
                              round_num: int,
                              proposer_id: bytes) -> 'Data':
        raise NotImplementedError

    @abstractmethod
    async def create_none_data(self,
                               term_num: int,
                               round_num: int,
                               proposer_id: bytes) -> 'Data':
        raise NotImplementedError

    @abstractmethod
    async def create_data_verifier(self) -> 'DataVerifier':
        raise NotImplementedError
