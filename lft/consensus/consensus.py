from typing import TYPE_CHECKING

from lft.consensus.layers.order import OrderLayer
from lft.consensus.layers.sync import SyncLayer
from lft.consensus.layers.round import RoundLayer

if TYPE_CHECKING:
    from lft.event import EventSystem
    from lft.consensus.messages.data import DataFactory
    from lft.consensus.messages.vote import VoteFactory


class Consensus:
    def __init__(self, event_system: 'EventSystem', node_id: bytes,
                 data_factory: 'DataFactory', vote_factory: 'VoteFactory'):
        self._round_layer = RoundLayer(
            node_id, event_system, data_factory, vote_factory
        )
        self._sync_layer = SyncLayer(
            self._round_layer, node_id, event_system, data_factory, vote_factory
        )
        self._order_layer = OrderLayer(
            self._sync_layer, node_id, event_system, data_factory, vote_factory
        )

    def __del__(self):
        self.close()

    def close(self):
        self._order_layer.close()



