from typing import TYPE_CHECKING
from lft.consensus.layers.async_.async_layer import AsyncLayer

if TYPE_CHECKING:
    from lft.event import EventSystem
    from lft.consensus.data import ConsensusDataFactory, ConsensusVoteFactory


class Consensus:
    def __init__(self, event_system: 'EventSystem', node_id: bytes,
                 data_factory: 'ConsensusDataFactory', vote_factory: 'ConsensusVoteFactory'):
        self.event_system = event_system
        self.data_factory = data_factory
        self.vote_factory = vote_factory
        self.node_id = node_id

        self._async_layer = AsyncLayer(node_id, event_system, data_factory, vote_factory)

    def __del__(self):
        self.close()

    def close(self):
        self._async_layer.close()
