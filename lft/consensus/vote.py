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


class Votes:
    def __init__(self, data_id: bytes, term_num: int, round_num: int):
        self._data_id: bytes = data_id
        self._term_num: int = term_num
        self._round_num: int = round_num
        self._voters = set()
        self._votes: List['Vote'] = []
        self._is_none = None

    @property
    def data_id(self) -> bytes:
        return self._data_id

    @property
    def term_num(self) -> int:
        return self._term_num

    @property
    def round_num(self) -> int:
        return self._round_num

    @property
    def votes(self) -> Sequence['Vote']:
        return self._votes

    def __len__(self):
        return len(self._votes)

    def add_vote(self, vote: 'Vote'):
        if vote.voter_id not in self._voters:
            if vote.data_id == self._data_id:
                if self._is_none is None:
                    self._is_none = True if vote.is_none() else False
                self._votes.append(vote)
                self._voters.add(vote.voter_id)

    def serialize(self, voters: Sequence[bytes]) -> List:
        votes = [b'' for x in voters]
        for vote in self._votes:
            try:
                vote_index = voters.index(vote.voter_id)
            except ValueError as e:
                print(f"Unknown voter : {vote.voter_id}")
            else:
                votes[vote_index] = vote
        return votes

    @classmethod
    def deserialize(cls: Type[T], votes: Sequence) -> T:
        deserialized_obj = None
        for vote in votes:
            if isinstance(vote, Vote):
                if not deserialized_obj:
                    deserialized_obj = cls(data_id=vote.data_id,
                                           term_num=vote.term_num,
                                           round_num=vote.round_num)
                deserialized_obj.add_vote(vote)
        return deserialized_obj

    def is_none(self) -> bool:
        if self._is_none is None:
            raise ValueError("Unknown votes status")
        return self._is_none


class EmptyVotes(Votes):
    def __init__(self):
        super().__init__(b'', 0, 0)

    def add_vote(self, vote: 'Vote'):
        raise NotImplementedError

    def serialize(self, voters: Sequence[bytes]) -> List:
        raise NotImplementedError

    @classmethod
    def deserialize(cls: Type[T], votes: Sequence) -> T:
        raise NotImplementedError


class VoteCounter:
    def __init__(self):
        self._majority_id: bytes = b''
        self._votes: Dict[bytes, 'Votes'] = {
            self._majority_id: EmptyVotes()
        }
        self._voters: Set[bytes] = set()

    @property
    def majority_id(self) -> bytes:
        return self._majority_id

    @property
    def majority_votes(self) -> Votes:
        return self._votes[self._majority_id]

    @property
    def majority_counts(self) -> int:
        return len(self.majority_votes)

    @property
    def voter_counts(self) -> int:
        return len(self._voters)

    def add_vote(self, vote: Vote):
        if not vote.is_not():
            votes = self._votes.get(vote.data_id)
            if not votes:
                self._votes[vote.data_id] = Votes(vote.data_id, vote.term_num, vote.round_num)
                votes = self._votes.get(vote.data_id)
            votes.add_vote(vote)
            self._update_majority(vote.data_id)
        self._voters.add(vote.voter_id)

    def _update_majority(self, data_id: bytes):
        if len(self._votes[data_id]) > self.majority_counts:
            self._majority_id = data_id
