from typing import Sequence, Tuple
from unittest.mock import MagicMock

from lft.app.data import DefaultDataFactory, DefaultData
from lft.app.term import RotateTermFactory
from lft.app.vote import DefaultVoteFactory
from lft.consensus.events import InitializeEvent, StartRoundEvent
from lft.consensus.layers import OrderLayer, SyncLayer
from lft.event import EventSystem


async def setup_order_layer() -> Tuple[OrderLayer, SyncLayer, Sequence[bytes], EventSystem]:
    mock_event_system = MagicMock(EventSystem())

    voters = [b'1', b'2', b'3', b'4']
    my_id = voters[0]

    mock_sync_layer = MagicMock(SyncLayer(
        round_layer=MagicMock(),
        node_id=my_id,
        event_system=mock_event_system,
        data_factory=DefaultDataFactory(my_id),
        vote_factory=DefaultVoteFactory(my_id),
        term_factory=RotateTermFactory(1)
    ))
    order_layer = OrderLayer(sync_layer=MagicMock,
                             async_layer=mock_sync_layer,
                             node_id=my_id,
                             event_system=mock_event_system,
                             data_factory=DefaultDataFactory(my_id),
                             vote_factory=DefaultVoteFactory(my_id),
                             term_factory=RotateTermFactory(1))

    genesis_data = DefaultData(
        id_=b'genesis',
        prev_id=None,
        proposer_id=voters[0],
        number=0,
        term_num=0,
        round_num=0,
        prev_votes=[]
    )

    order_layer._on_event_initialize(
        InitializeEvent(
            term_num=0,
            round_num=0,
            candidate_data=genesis_data,
            votes=[],
            voters=voters
        )
    )
    order_layer._on_event_start_round(
        StartRoundEvent(
            term_num=0,
            round_num=1,
            voters=voters
        )
    )

    return order_layer, mock_sync_layer, voters, mock_event_system
