from lft.consensus.data import ConsensusDataVerifier, ConsensusVoteVerifier


class DefaultConsensusDataVerifier(ConsensusDataVerifier):
    async def verify(self, data: 'DefaultConsensusData'):
        pass


class DefaultConsensusVoteVerifier(ConsensusVoteVerifier):
    async def verify(self, vote: 'DefaultConsensusVote'):
        pass
