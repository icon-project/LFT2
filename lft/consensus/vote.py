from abc import ABC, abstractmethod
from typing import Type, Sequence, List, TypeVar, Dict, Set

from lft.serialization import Serializable

T = TypeVar("T")


class Vote(Serializable):
    @property
    @abstractmethod
    def id(self) -> bytes:
        raise NotImplementedError

    @property
    @abstractmethod
    def data_id(self) -> bytes:
        raise NotImplementedError

    @property
    @abstractmethod
    def commit_id(self) -> bytes:
        raise NotImplementedError

    @property
    @abstractmethod
    def voter_id(self) -> bytes:
        raise NotImplementedError

    @property
    @abstractmethod
    def term_num(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def round_num(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def is_not(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def is_none(self) -> bool:
        raise NotImplementedError

    def __eq__(self, other):
        return self.id == other.id \
               and self.data_id == other.data_id \
               and self.commit_id == other.commit_id \
               and self.voter_id == other.voter_id \
               and self.term_num == other.term_num \
               and self.round_num == other.round_num

    def __hash__(self):
        return int.from_bytes(self.id, "big")


class VoteVerifier(ABC):
    @abstractmethod
    async def verify(self, vote: 'Vote'):
        raise NotImplementedError


class VoteFactory(ABC):
    async def create_vote(self, data_id: bytes, commit_id: bytes, term_num: int, round_num: int) -> 'Vote':
        raise NotImplementedError

    async def create_not_vote(self, voter_id: bytes, term_num: int, round_num: int) -> 'Vote':
        raise NotImplementedError

    async def create_none_vote(self, term_num: int, round_num: int) -> 'Vote':
        raise NotImplementedError

    async def create_vote_verifier(self) -> 'VoteVerifier':
        raise NotImplementedError
