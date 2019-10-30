from typing import Sequence, Tuple
from unittest.mock import MagicMock

from lft.app.data import DefaultDataFactory, DefaultData
from lft.app.term import RotateTermFactory
from lft.app.vote import DefaultVoteFactory
from lft.consensus.events import InitializeEvent, StartRoundEvent
from lft.consensus.layers import OrderLayer
from lft.event import EventSystem


async def setup_order_layer() -> Tuple[OrderLayer, MagicMock, Sequence[bytes], EventSystem]:
    mock_sync_layer = MagicMock()
    voters = [b'1', b'2', b'3', b'4']
    my_id = voters[0]
    event_system = EventSystem()
    order_layer = OrderLayer(sync_layer=MagicMock,
                             async_layer=mock_sync_layer,
                             node_id=my_id,
                             event_system=event_system,
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

    await event_system.simulator.raise_event(
        InitializeEvent(
            term_num=0,
            round_num=0,
            candidate_data=genesis_data,
            votes=[],
            voters=voters
        )
    )

    await event_system.simulator.raise_event(
        StartRoundEvent(
            term_num=0,
            round_num=1,
            voters=voters
        )
    )
    return order_layer, mock_sync_layer, voters, event_system
