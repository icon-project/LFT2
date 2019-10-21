import os
from typing import Type, TypeVar
from lft.consensus.vote import Vote, VoteVerifier, VoteFactory

T = TypeVar("T")


class DefaultVote(Vote):
    NoneVote = bytes(16)

    def __init__(self, id_: bytes, data_id: bytes, commit_id: bytes, voter_id: bytes, term_num: int, round_num: int):
        self._id = id_
        self._data_id = data_id
        self._commit_id = commit_id
        self._voter_id = voter_id
        self._term_num = term_num
        self._round_num = round_num

    @property
    def id(self) -> bytes:
        return self._id

    @property
    def data_id(self) -> bytes:
        return self._data_id

    @property
    def commit_id(self) -> bytes:
        return self._commit_id

    @property
    def term_num(self) -> int:
        return self._term_num

    @property
    def voter_id(self) -> bytes:
        return self._voter_id

    @property
    def round_num(self) -> int:
        return self._round_num

    def is_not(self) -> bool:
        return self._data_id == self._voter_id

    def is_none(self) -> bool:
        return self._data_id == self.NoneVote

    def _serialize(self) -> dict:
        return {
            "id": self.id,
            "data_id": self.data_id,
            "commit_id": self.commit_id,
            "voter_id": self.voter_id,
            "term": self.term_num,
            "round": self.round_num,
        }

    @classmethod
    def _deserialize(cls: Type[T], **kwargs) -> T:
        return DefaultVote(
            id_=kwargs["id"],
            data_id=kwargs["data_id"],
            commit_id=kwargs["commit_id"],
            voter_id=kwargs["voter_id"],
            term_num=kwargs["term"],
            round_num=kwargs["round"]
        )


class DefaultVoteVerifier(VoteVerifier):
    async def verify(self, vote: 'DefaultVote'):
        pass


class DefaultVoteFactory(VoteFactory):
    def __init__(self, node_id: bytes):
        self._node_id = node_id

    def _create_id(self) -> bytes:
        return os.urandom(16)

    async def create_vote(self,
                          data_id: bytes, commit_id: bytes, term_num: int, round_num: int) -> DefaultVote:
        return DefaultVote(self._create_id(), data_id, commit_id, self._node_id, term_num, round_num)

    async def create_not_vote(self, voter_id: bytes, term_num: int, round_num: int) -> DefaultVote:
        return DefaultVote(self._create_id(), voter_id, voter_id, voter_id, term_num, round_num)

    async def create_none_vote(self, term_num: int, round_num: int) -> DefaultVote:
        return DefaultVote(self._create_id(),
                                    DefaultVote.NoneVote,
                                    DefaultVote.NoneVote,
                                    self._node_id,
                                    term_num,
                                    round_num)

    async def create_vote_verifier(self) -> DefaultVoteVerifier:
        return DefaultVoteVerifier()