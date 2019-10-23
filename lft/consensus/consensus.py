from typing import TYPE_CHECKING
from lft.consensus.layers.async_.async_layer import AsyncLayer
from lft.consensus.layers.sync.sync_layer import SyncLayer

if TYPE_CHECKING:
    from lft.event import EventSystem
    from lft.consensus.data import DataFactory
    from lft.consensus.vote import VoteFactory
    from lft.consensus.term import TermFactory


class Consensus:
    def __init__(self, event_system: 'EventSystem', node_id: bytes,
                 data_factory: 'DataFactory', vote_factory: 'VoteFactory', term_factory: 'TermFactory'):
        self._sync_layer = SyncLayer(
            node_id, event_system, data_factory, vote_factory, term_factory
        )
        self._async_layer = AsyncLayer(
            self._sync_layer, node_id, event_system, data_factory, vote_factory, term_factory
        )

    def __del__(self):
        self.close()

    def close(self):
        self._async_layer.close()
        self._sync_layer.close()
