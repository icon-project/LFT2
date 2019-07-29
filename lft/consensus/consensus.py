from typing import TYPE_CHECKING
from lft.consensus.layers.async_.async_layer import AsyncLayer

if TYPE_CHECKING:
    from lft.event import EventSystem
    from lft.consensus.data import ConsensusDataFactory, ConsensusVoteFactory


class Consensus:
    def __init__(self, event_system: 'EventSystem', id_: bytes,
                 data_factory: 'ConsensusDataFactory', vote_factory: 'ConsensusVoteFactory'):
        self.event_system = event_system
        self.data_factory = data_factory
        self.vote_factory = vote_factory
        self.id = id_

        self._async_layer = AsyncLayer(id_, event_system, data_factory, vote_factory)
