import logging
from typing import Optional

from lft.consensus.data import DataFactory
from lft.consensus.events import InitializeEvent, StartRoundEvent, DoneRoundEvent, ReceivedDataEvent, ReceivedVoteEvent
from lft.consensus.layers import SyncLayer, AsyncLayer
from lft.consensus.term import TermFactory, Term
from lft.consensus.vote import VoteFactory
from lft.event import EventRegister, EventSystem


class OrderLayer(EventRegister):
    def __init__(self,
                 sync_layer: SyncLayer,
                 async_layer: AsyncLayer,
                 node_id: bytes,
                 event_system: EventSystem,
                 data_factory: DataFactory,
                 vote_factory: VoteFactory,
                 term_factory: TermFactory):
        super().__init__(event_system.simulator)
        self._sync_layer = sync_layer
        self._node_id = node_id
        self._event_system = event_system
        self._data_factory = data_factory
        self._vote_factory = vote_factory
        self._term_factory = term_factory
        self._logger = logging.getLogger(node_id.hex())

        self._term: Optional[Term] = None
        self._round_num = -1
        self._candidate_num = -1

        self._vote_timeout_started = False

    _handler_prototypes = {
        InitializeEvent: _on_event_initialize,
        StartRoundEvent: _on_event_start_round,
        DoneRoundEvent: _on_event_done_round,
        ReceivedDataEvent: _on_event_received_consensus_data,
        ReceivedVoteEvent: _on_event_received_consensus_vote
    }
