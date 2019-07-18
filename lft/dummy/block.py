from loopchain.blockchain.blocks import Block
from loopchain.blockchain.blocks.v0_3 import BlockBuilder, BlockVerifier
from loopchain.blockchain.transactions import TransactionVersioner

from lft.consensus.factories import ConsensusData, ConsensusDataVerifier, ConsensusDataFactory

tx_versioner = TransactionVersioner()


class BlockFactory(ConsensusDataFactory):
    def __init__(self, blockchain):
        self.blockchain = blockchain

    async def create_data(self) -> 'ConsensusData':
        builder = BlockBuilder(tx_versioner)
        return builder.build()


class BlockVerifierAdapter:
    def __init__(self, block, prev_block, blockchain):
        self.block = block
        self.prev_block = prev_block
        self.blockchain = blockchain

    async def verify(self):
        verifier = BlockVerifier(tx_versioner)
        verifier.verify(self.block, self.prev_block)


ConsensusData.register(Block)
ConsensusDataVerifier.register(BlockVerifierAdapter)
