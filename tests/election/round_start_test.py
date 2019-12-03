import pytest
from lft.consensus.events import BroadcastDataEvent, ReceiveDataEvent
from tests.election.setup_election import setup_election, CANDIDATE_ID

PEER_NUM = 7


@pytest.mark.asyncio
async def test_round_start():
    # GIVEN
    event_system, election, voters = await setup_election(PEER_NUM)

    # WHEN
    election._round_num = voters.index(election._node_id)
    await election.round_start()

    # THEN
    broadcast_data_event = event_system.simulator.raise_event.call_args_list[0][0][0]
    assert isinstance(broadcast_data_event, BroadcastDataEvent)
    assert broadcast_data_event.data.prev_id == CANDIDATE_ID
    assert broadcast_data_event.data.round_num == election._round_num
    assert broadcast_data_event.data.proposer_id == election._node_id
    assert broadcast_data_event.data.epoch_num == election._epoch.num
    assert broadcast_data_event.data.number == 1

    receive_data_event = event_system.simulator.raise_event.call_args_list[1][0][0]
    assert isinstance(receive_data_event, ReceiveDataEvent)
    assert receive_data_event.data == broadcast_data_event.data
