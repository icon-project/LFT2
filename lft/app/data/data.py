from typing import Sequence

from lft.consensus.data import ConsensusVote, ConsensusData


class DefaultConsensusData(ConsensusData):
    def __init__(self,
                 id_: bytes,
                 prev_id: bytes,
                 proposer_id: bytes,
                 number: int,
                 term_num: int,
                 round_num: int,
                 prev_votes: Sequence['DefaultConsensusVote'] = ()):
        self._id = id_
        self._prev_id = prev_id
        self._proposer_id = proposer_id
        self._number = number
        self._term_num = term_num
        self._round_num = round_num
        self._prev_votes: Sequence['DefaultConsensusVote'] = prev_votes

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
    def prev_votes(self) -> Sequence['DefaultConsensusVote']:
        return self._prev_votes

    def is_not(self) -> bool:
        return self._id == self._proposer_id


class DefaultConsensusVote(ConsensusVote):
    NoneVote = bytes(16)

    def __init__(self, id_: bytes, data_id: bytes, voter_id: bytes, term_num: int, round_num: int):
        self._id = id_
        self._data_id = data_id
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
