from abc import ABC, abstractmethod
from typing import Iterable

from lft.consensus.messages.message import Message, MessagePool

__all__ = ("Vote", "VoteFactory", "VotePool", "VoteVerifier")


class Vote(Message):
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
    def consensus_id(self) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def is_none(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def is_lazy(self) -> bool:
        raise NotImplementedError

    def is_real(self) -> bool:
        return not self.is_lazy()

    def __eq__(self, other):
        return self.id == other.id \
               and self.data_id == other.data_id \
               and self.commit_id == other.commit_id \
               and self.voter_id == other.voter_id \
               and self.epoch_num == other.epoch_num \
               and self.round_num == other.round_num

    def __hash__(self):
        return int.from_bytes(self.id, "big")


class VoteVerifier(ABC):
    @abstractmethod
    async def verify(self, vote: 'Vote'):
        raise NotImplementedError


class VoteFactory(ABC):
    async def create_vote(self, data_id: bytes, commit_id: bytes, epoch_num: int, round_num: int) -> 'Vote':
        raise NotImplementedError

    def create_none_vote(self, epoch_num: int, round_num: int) -> 'Vote':
        raise NotImplementedError

    def create_lazy_vote(self, voter_id: bytes, epoch_num: int, round_num: int) -> 'Vote':
        raise NotImplementedError

    async def create_vote_verifier(self) -> 'VoteVerifier':
        raise NotImplementedError


class VotePool(MessagePool):
    def add_vote(self, vote: Vote):
        self.add_message(vote)

    def get_vote(self, vote_id) -> Vote:
        return self.get_message(vote_id)

    def get_votes(self, epoch_num: int, round_num: int) -> Iterable[Vote]:
        return self.get_messages(epoch_num, round_num)

    def prune_vote(self, latest_epoch_num: int, latest_round_num: int):
        super().prune_message(latest_epoch_num, latest_round_num)
