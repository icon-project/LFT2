import os
import pytest
from lft.consensus.events import ReceivedConsensusDataEvent, ReceivedConsensusVoteEvent, DoneRoundEvent
from .conftest import start_event_system


@pytest.mark.asyncio
@pytest.mark.parametrize("init_round_num, voter_num", [(0, i) for i in range(4, 100)])
async def test_async_layer_basic(async_layer_items, init_round_num, voter_num: int):
    node_id, event_system, async_layer, voters, data_factory, vote_factories = async_layer_items

    data = await data_factory.create_data(0, os.urandom(16), 0, 0, [])
    event = ReceivedConsensusDataEvent(data)
    event_system.simulator.raise_event(event)

    votes = []
    for vote_factory in vote_factories[1:]:
        vote = await vote_factory.create_vote(data.id, b'', data.term_num, data.round_num)
        votes.append(vote)
        event = ReceivedConsensusVoteEvent(vote)
        event.deterministic = False
        event_system.simulator.raise_event(event)

    await start_event_system(event_system)

    assert data is async_layer._data_dict[0][data.id]
    assert len(async_layer._data_dict) == 1
    assert len(async_layer._data_dict[0]) == 1

    for voter, vote in zip(voters[1:], votes):
        assert vote is async_layer._vote_dict[init_round_num][voter][vote.id]
        assert len(async_layer._vote_dict[init_round_num][voter]) == 1
    assert len(async_layer._vote_dict) == 1
    assert len(async_layer._vote_dict[init_round_num]) == voter_num - 1

    event = DoneRoundEvent(True, 0, init_round_num + 3, data, data, None)
    event_system.simulator.raise_event(event)

    await start_event_system(event_system)

    assert init_round_num not in async_layer._data_dict
    assert init_round_num not in async_layer._vote_dict
