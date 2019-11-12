import pytest

from lft.app.data import DefaultData
from lft.app.term import RotateTerm
from lft.consensus.events import ReceiveDataEvent, RoundStartEvent
from tests.order_layer.setup_order_layer import setup_order_layer


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
    await order_layer._on_event_receive_data(
        ReceiveDataEvent(data)
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
    await order_layer._on_event_receive_data(
        ReceiveDataEvent(data)
    )

    # THEN
    sync_layer.receive_data.assert_not_called()


@pytest.mark.asyncio
async def test_receive_past_term_data():
    order_layer, sync_layer, voters, event_system = await setup_order_layer()
    await order_layer._on_event_round_start(
        RoundStartEvent(
            term=RotateTerm(1, voters),
            round_num=0
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
    await order_layer._on_event_receive_data(
        ReceiveDataEvent(data)
    )

    # THEN
    sync_layer.receive_data.assert_not_called()
    assert len(order_layer._get_datums(1)) == 0


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
    await order_layer._on_event_receive_data(
        ReceiveDataEvent(data)
    )

    # THEN
    datums = order_layer._get_datums(10)
    assert len(datums) == 1
    assert next(iter(datums)) == data


@pytest.mark.asyncio
async def test_receive_future_term_data():
    order_layer, sync_layer, voters, event_system = await setup_order_layer()
    await order_layer._on_event_round_start(
        RoundStartEvent(
            term=RotateTerm(1, voters),
            round_num=0
        )
    )
    data = DefaultData(id_=b'first',
                       prev_id=b'genesis',
                       proposer_id=voters[1],
                       number=1,
                       term_num=10,
                       round_num=11,
                       prev_votes=[])
    # WHEN
    await order_layer._on_event_receive_data(
        ReceiveDataEvent(data)
    )

    # THEN
    sync_layer.receive_data.assert_not_called()
    assert len(order_layer._get_datums(11)) == 0


@pytest.mark.asyncio
async def test_receive_past_term_data():
    order_layer, sync_layer, voters, event_system = await setup_order_layer()
    await order_layer._on_event_round_start(
        RoundStartEvent(
            term=RotateTerm(1, voters),
            round_num=0
        )
    )
    data = DefaultData(id_=b'first',
                       prev_id=b'genesis',
                       proposer_id=voters[3],
                       number=1,
                       term_num=0,
                       round_num=1,
                       prev_votes=[])
    # WHEN
    await order_layer._on_event_receive_data(
        ReceiveDataEvent(data)
    )

    # THEN
    sync_layer.receive_data.assert_not_called()
    assert len(order_layer._get_datums(1)) == 0
