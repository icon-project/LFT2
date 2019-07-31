from abc import ABC, abstractmethod
from typing import Type, Sequence
from lft.serialization import Serializable


class ConsensusDataFactory(ABC):
    @abstractmethod
    async def create_data(self,
                          data_number: int,
                          prev_id: bytes,
                          term_num: int,
                          round_num: int) -> 'ConsensusData':
        raise NotImplementedError

    @abstractmethod
    async def create_not_data(self,
                              data_number: int,
                              term_num: int,
                              round_num: int) -> 'ConsensusData':
        raise NotImplementedError

    @abstractmethod
    async def create_data_verifier(self) -> 'ConsensusDataVerifier':
        raise NotImplementedError


class ConsensusVoteFactory(ABC):
    async def create_vote(self, data_id: bytes, term_num: int, round_num: int) -> 'ConsensusVote':
        raise NotImplementedError

    async def create_not_vote(self, voter_id: bytes, term_num: int, round_num: int) -> 'ConsensusVote':
        raise NotImplementedError

    async def create_none_vote(self, term_num: int, round_num: int) -> 'ConsensusVote':
        raise NotImplementedError

    async def create_vote_verifier(self) -> 'ConsensusVoteVerifier':
        raise NotImplementedError


class ConsensusDataVerifier(ABC):
    @abstractmethod
    async def verify(self, data: 'ConsensusData'):
        raise NotImplementedError


class ConsensusVoteVerifier(ABC):
    @abstractmethod
    async def verify(self, vote: 'ConsensusVote'):
        raise NotImplementedError


class ConsensusVote(Serializable):
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
