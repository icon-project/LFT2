from unittest.mock import MagicMock

import pytest

from lft.app.data import DefaultData
from lft.consensus.events import ReceivedDataEvent
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
    given_data = DefaultData(id_=b'first',
                             prev_id=b'genesis',
                             proposer_id=voters[1],
                             number=1,
                             term_num=0,
                             round_num=1,
                             prev_votes=[])

    def verify_call(data):
        assert data == given_data
        raise IsCalled()

    sync_layer.receive_data = verify_call
    # WHEN
    try:
        await event_system.simulator.raise_event(ReceivedDataEvent(given_data))
    except IsCalled:
        pass
    else:
        assert False
