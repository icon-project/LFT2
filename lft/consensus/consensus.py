from typing import TYPE_CHECKING
from lft.consensus.layers.async_.async_layer import AsyncLayer
from lft.consensus.layers.sync.sync_layer import SyncLayer
from lft.consensus.term.factories import TermFactory

if TYPE_CHECKING:
    from lft.event import EventSystem
    from lft.consensus.data import DataFactory, VoteFactory


class Consensus:
    def __init__(self, event_system: 'EventSystem', node_id: bytes,
                 data_factory: 'DataFactory', vote_factory: 'VoteFactory',
                 term_factory: 'TermFactory'):
        self.event_system = event_system
        self.data_factory = data_factory
        self.vote_factory = vote_factory
        self.node_id = node_id

        self._async_layer = AsyncLayer(node_id, event_system, data_factory, vote_factory, term_factory)
        self._sync_layer = SyncLayer(node_id, event_system, data_factory, vote_factory, term_factory)

    def __del__(self):
        self.close()

    def close(self):
        self._async_layer.close()
        self._sync_layer.close()
