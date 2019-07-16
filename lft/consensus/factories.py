from abc import ABC, abstractmethod
from typing import Sequence


class ConsensusDataFactory(ABC):
    # node id를 할당해주면 어떨까
    @abstractmethod
    async def create_data(self) -> 'ConsensusData':
        raise NotImplementedError

    @abstractmethod
    async def create_not_data(self) -> 'ConsensusData':
        raise NotImplementedError

    @abstractmethod
    async def create_data_verifier(self) -> 'ConsensusDataVerifier':
        raise NotImplementedError


class ConsensusVoteFactory(ABC):
    # node id를 할당해주면 어떨까
    async def create_vote(self, voter_id: bytes) -> 'ConsensusVote':
        raise NotImplementedError

    async def create_not_vote(self, voter_id: bytes) -> 'ConsensusVote':
        raise NotImplementedError

    async def create_vote_verifier(self) -> 'ConsensusVoteVerifier':
        raise NotImplementedError


class ConsensusDataVerifier(ABC):
    @abstractmethod
    async def verify(self):
        raise NotImplementedError


class ConsensusVoteVerifier(ABC):
    @abstractmethod
    async def verify(self):
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
    def term_num(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def voter_id(self) -> bytes:
        raise NotImplementedError

    @property
    @abstractmethod
    def round_num(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def __bool__(self) -> bool:
        """
        Determine if it is NotVote
        if not vote:
            # NotVote
        """
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
    def proposer(self) -> bytes:
        raise NotImplementedError

    @property
    @abstractmethod
    def term_num(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def number(self) -> int:
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
    def __bool__(self) -> bool:
        """
        Determine if it is NotData
        if not data:
            # NotData
        :return:
        """
