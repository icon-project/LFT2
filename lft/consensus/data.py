from abc import ABC, abstractmethod
from typing import Sequence

from lft.consensus.vote import ConsensusVote
from lft.serialization import Serializable


class ConsensusData(Serializable):
    @property
    @abstractmethod
    def id(self) -> bytes:
        raise NotImplementedError

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
    def term_num(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def round_num(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def prev_votes(self) -> Sequence['ConsensusVote']:
        raise NotImplementedError

    @abstractmethod
    def is_not(self) -> bool:
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


class ConsensusDataVerifier(ABC):
    @abstractmethod
    async def verify(self, data: 'ConsensusData'):
        raise NotImplementedError

    async def add_vote(self, vote: 'ConsensusVote'):
        raise NotImplementedError


class ConsensusDataFactory(ABC):
    @abstractmethod
    async def create_data(self,
                          data_number: int,
                          prev_id: bytes,
                          term_num: int,
                          round_num: int,
                          prev_votes: Sequence['ConsensusVote']) -> 'ConsensusData':
        raise NotImplementedError

    @abstractmethod
    async def create_not_data(self,
                              data_number: int,
                              term_num: int,
                              round_num: int,
                              proposer_id: bytes) -> 'ConsensusData':
        raise NotImplementedError

    @abstractmethod
    async def create_data_verifier(self) -> 'ConsensusDataVerifier':
        raise NotImplementedError
