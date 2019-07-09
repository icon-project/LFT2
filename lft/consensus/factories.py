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
    def term(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def round(self) -> int:
        raise NotImplementedError

    @abstractmethod
    async def verify(self):
        raise NotImplementedError


class ConsensusData(ABC):
    @property
    @abstractmethod
    def id(self) -> bytes:
        raise NotImplementedError

    @property
    @abstractmethod
    def prev_id(self) -> bytes:
        raise NotImplementedError

    @property
    @abstractmethod
    def leader(self) -> bytes:
        raise NotImplementedError

    @property
    @abstractmethod
    def terms(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def number(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def round(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def votes(self) -> 'ConsensusVotes':
        raise NotImplementedError
