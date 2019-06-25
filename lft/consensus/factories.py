from abc import ABC, abstractmethod
from typing import Optional


class ConsensusDataFactory(ABC):
    @abstractmethod
    async def create_data(self) -> 'ConsensusData':
        raise NotImplementedError

    @abstractmethod
    async def create_data_verifier(self, data: 'ConsensusData') -> 'ConsensusDataVerifier':
        raise NotImplementedError


class ConsensusVoteFactory(ABC):
    async def create_vote(self) -> 'ConsensusVote':
        raise NotImplementedError

    async def create_votes(self) -> 'ConsensusVotes':
        raise NotImplementedError


class ConsensusData(ABC):
    @abstractmethod
    @property
    def id(self):
        raise NotImplementedError


class ConsensusDataVerifier(ABC):
    @abstractmethod
    async def verify(self):
        raise NotImplementedError


class ConsensusVotes(ABC):
    @abstractmethod
    async def add_vote(self, vote: 'ConsensusVotes'):
        raise NotImplementedError

    @abstractmethod
    async def verify(self):
        raise NotImplementedError

    @abstractmethod
    async def get_result(self) -> Optional[bool]:
        raise NotImplementedError


class ConsensusVote(ABC):
    @abstractmethod
    @property
    def id(self) -> bytes:
        raise NotImplementedError

    @abstractmethod
    @property
    def data_id(self) -> bytes:
        raise NotImplementedError

    @abstractmethod
    @property
    def era(self) -> int:
        raise NotImplementedError

    @abstractmethod
    @property
    def round(self) -> int:
        raise NotImplementedError

    @abstractmethod
    async def verify(self):
        raise NotImplementedError

