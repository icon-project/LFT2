import os

from lft.consensus.default_data.data import DefaultConsensusData, DefaultConsensusVote
from lft.consensus.default_data.verifier import DefaultConsensusDataVerifier, DefaultConsensusVoteVerifier
from lft.consensus.factories import *


class DefaultConsensusDataFactory(ConsensusDataFactory):
    def __init__(self, node_id: bytes):
        self._node_id = node_id

    def _create_id(self) -> bytes:
        return os.urandom(16)

    async def create_data(self,
                          data_number: int,
                          prev_id: bytes,
                          term_num: int,
                          round_num: int) -> DefaultConsensusData:
        return DefaultConsensusData(self._create_id(), prev_id, self._node_id, data_number, term_num, round_num)

    async def create_not_data(self,
                              data_number: int,
                              term_num: int,
                              round_num: int) -> DefaultConsensusData:
        return DefaultConsensusData(self._node_id, self._node_id, self._node_id, data_number, term_num, round_num)

    async def create_data_verifier(self) -> DefaultConsensusDataVerifier:
        return DefaultConsensusDataVerifier()


class DefaultConsensusVoteFactory(ConsensusVoteFactory):
    def __init__(self, node_id: bytes):
        self._node_id = node_id

    def _create_id(self) -> bytes:
        return os.urandom(16)

    async def create_vote(self, data_id: bytes, term_num: int, round_num: int) -> DefaultConsensusVote:
        return DefaultConsensusVote(self._create_id(), data_id, self._node_id, term_num, round_num)

    async def create_not_vote(self, voter_id: bytes, term_num: int, round_num: int) -> DefaultConsensusVote:
        return DefaultConsensusVote(self._create_id(), voter_id, voter_id, term_num, round_num)

    async def create_none_vote(self, term_num: int, round_num: int) -> DefaultConsensusVote:
        return DefaultConsensusVote(self._create_id(),
                                    DefaultConsensusVote.NoneVote,
                                    self._node_id,
                                    term_num,
                                    round_num)

    async def create_vote_verifier(self) -> DefaultConsensusVoteVerifier:
        return DefaultConsensusVoteVerifier()
