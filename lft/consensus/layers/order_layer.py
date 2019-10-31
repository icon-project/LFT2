import logging
from typing import Optional, Sequence

from lft.consensus.data import DataFactory, Data
from lft.consensus.events import InitializeEvent, StartRoundEvent, DoneRoundEvent, ReceivedDataEvent, ReceivedVoteEvent
from lft.consensus.layers import SyncLayer, RoundLayer
from lft.consensus.term import Term
from lft.consensus.vote import VoteFactory
from lft.event import EventRegister, EventSystem


class OrderLayer(EventRegister):
    def __init__(self,
                 sync_layer: SyncLayer,
                 round_layer: RoundLayer,
                 node_id: bytes,
                 event_system: EventSystem,
                 data_factory: DataFactory,
                 vote_factory: VoteFactory):
        super().__init__(event_system.simulator)
        self._sync_layer = sync_layer
        self._order_layer = round_layer
        self._node_id = node_id
        self._event_system = event_system
        self._data_factory = data_factory
        self._vote_factory = vote_factory
        self._logger = logging.getLogger(node_id.hex())

        self._term: Optional[Term] = None
        self._round_num = -1
        self._candidate_num = -1

        self._vote_timeout_started = False

    def _on_event_initialize(self, event: InitializeEvent):
        self._initialize(
            term=event.term,
            round_num=event.round_num,
            candidate_data=event.candidate_data,
            votes=event.votes
        )

    def _on_event_start_round(self, event: StartRoundEvent):
        pass

    def _on_event_done_round(self, event: DoneRoundEvent):
        pass

    def _on_event_received_data(self, event: ReceivedDataEvent):
        pass

    def _on_event_received_vote(self, event: ReceivedVoteEvent):
        pass

    def _initialize(self, term: Term, round_num: int, candidate_data: Data, votes: Sequence['Vote']):
        pass

    _handler_prototypes = {
        InitializeEvent: _on_event_initialize,
        StartRoundEvent: _on_event_start_round,
        DoneRoundEvent: _on_event_done_round,
        ReceivedDataEvent: _on_event_received_data,
        ReceivedVoteEvent: _on_event_received_vote
    }
