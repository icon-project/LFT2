import os
from typing import Sequence, Type, TypeVar
from lft.app.vote import DefaultVote
from lft.consensus.data import Data, DataVerifier, DataFactory

T = TypeVar("T")


class DefaultData(Data):
    def __init__(self,
                 id_: bytes,
                 prev_id: bytes,
                 proposer_id: bytes,
                 number: int,
                 term_num: int,
                 round_num: int,
                 prev_votes: Sequence['DefaultVote'] = ()):
        self._id = id_
        self._prev_id = prev_id
        self._proposer_id = proposer_id
        self._number = number
        self._term_num = term_num
        self._round_num = round_num
        self._prev_votes: Sequence['DefaultVote'] = prev_votes

    @property
    def id(self) -> bytes:
        return self._id

    @property
    def prev_id(self) -> bytes:
        return self._prev_id

    @property
    def proposer_id(self) -> bytes:
        return self._proposer_id

    @property
    def term_num(self) -> int:
        return self._term_num

    @property
    def number(self) -> int:
        return self._number

    @property
    def round_num(self) -> int:
        return self._round_num

    @property
    def prev_votes(self) -> Sequence['DefaultVote']:
        return self._prev_votes

    def is_not(self) -> bool:
        return self._id == self._proposer_id

    def _serialize(self) -> dict:
        return {
            "id": self.id,
            "prev_id": self.prev_id,
            "proposer_id": self.proposer_id,
            "number": self.number,
            "term": self.term_num,
            "round": self.round_num,
            "prev_votes": list(self.prev_votes)
        }

    @classmethod
    def _deserialize(cls: Type[T], **kwargs) -> T:
        return DefaultData(
            id_=kwargs["id"],
            prev_id=kwargs["prev_id"],
            proposer_id=kwargs["proposer_id"],
            number=kwargs["number"],
            term_num=kwargs["term"],
            round_num=kwargs["round"],
            prev_votes=tuple(kwargs["prev_votes"])
        )


class DefaultDataVerifier(DataVerifier):
    async def verify(self, data: 'DefaultData'):
        pass


class DefaultDataFactory(DataFactory):
    def __init__(self, node_id: bytes):
        self._node_id = node_id

    def _create_id(self) -> bytes:
        return os.urandom(16)

    async def create_data(self,
                          data_number: int,
                          prev_id: bytes,
                          term_num: int,
                          round_num: int,
                          prev_votes: Sequence['DefaultVote']) -> DefaultData:
        return DefaultData(self._create_id(), prev_id, self._node_id, data_number, term_num, round_num,
                                    prev_votes=prev_votes)

    async def create_not_data(self,
                              data_number: int,
                              term_num: int,
                              round_num: int,
                              proposer_id: bytes) -> DefaultData:
        return DefaultData(proposer_id, proposer_id, proposer_id, data_number, term_num, round_num)

    async def create_data_verifier(self) -> DefaultDataVerifier:
        return DefaultDataVerifier()

