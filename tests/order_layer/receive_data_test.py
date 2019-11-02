from unittest.mock import MagicMock

import pytest

from lft.app.data import DefaultData
from lft.app.term import RotateTerm
from lft.consensus.events import ReceivedDataEvent, StartRoundEvent
from tests.order_layer.setup_order_layer import setup_order_layer
from tests.test_exception import IsCalled


@pytest.mark.asyncio
async def test_receive_now_round_data():
    """ GIVEN initialized OrderLayer and now round data
    WHEN raises ReceiveData with GIVEN data
    THEN OrderLayer call SyncLayer.receive_data(data)
    """
    # GIVEN
    order_layer, sync_layer, voters, event_system = await setup_order_layer()
    data = DefaultData(id_=b'first',
                       prev_id=b'genesis',
                       proposer_id=voters[1],
                       number=1,
                       term_num=0,
                       round_num=1,
                       prev_votes=[])

    # WHEN
    order_layer._on_event_received_data(
        ReceivedDataEvent(data)
    )

    # THEN
    sync_layer.receive_data.assert_called_once_with(data)

@pytest.mark.asyncio
async def test_receive_past_round_data():
    # GIVEN
    order_layer, sync_layer, voters, event_system = await setup_order_layer()
    data = DefaultData(id_=b'first',
                       prev_id=b'genesis',
                       proposer_id=voters[1],
                       number=1,
                       term_num=0,
                       round_num=0,
                       prev_votes=[])

    # WHEN
    order_layer._on_event_received_data(
        ReceivedDataEvent(data)
    )

    # THEN
    sync_layer.receive_data.assert_not_called()

@pytest.mark.asyncio
async def test_receive_past_term_data():
    order_layer, sync_layer, voters, event_system = await setup_order_layer()
    order_layer._on_event_start_round(
        StartRoundEvent(
            term=RotateTerm(1, voters),
            round_num=1
        )
    )
    data = DefaultData(id_=b'first',
                       prev_id=b'genesis',
                       proposer_id=voters[1],
                       number=1,
                       term_num=0,
                       round_num=1,
                       prev_votes=[])
    # WHEN
    order_layer._on_event_received_data(
        ReceivedDataEvent(data)
    )

    # THEN
    sync_layer.receive_data.assert_not_called()


@pytest.mark.asyncio
async def test_receive_future_data():
    # GIVEN
    order_layer, sync_layer, voters, event_system = await setup_order_layer()
    data = DefaultData(id_=b'first',
                       prev_id=b'genesis',
                       proposer_id=voters[2],
                       number=2,
                       term_num=0,
                       round_num=10,
                       prev_votes=[])

    # WHEN
    order_layer._on_event_received_data(
        ReceivedDataEvent(data)
    )

    # THEN
    order_layer._get_messages(0, 10)[0] == data
