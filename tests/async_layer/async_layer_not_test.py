import os
import random
import pytest
from typing import cast
from lft.consensus.events import ReceivedConsensusDataEvent, ReceivedConsensusVoteEvent
from lft.app.data import DefaultConsensusVoteFactory
from .conftest import start_event_system

param_count = 10

voter_nums = [random.randint(4, 100) for _ in range(param_count)]
init_round_nums = [0] * param_count
parameters = list(zip(voter_nums, init_round_nums))


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num, init_round_num", parameters)
async def test_async_layer_not_data_early(async_layer_items,
                                          voter_num: int,
                                          init_round_num: int):
    node_id, event_system, async_layer, voters, data_factory, vote_factories = async_layer_items

    not_data = await data_factory.create_not_data(0, 0, init_round_num, voters[0])
    event = ReceivedConsensusDataEvent(not_data)
    event_system.simulator.raise_event(event)

    await start_event_system(event_system)
    assert not_data is async_layer._data_dict[init_round_num][not_data.id]

    data = await data_factory.create_data(0, os.urandom(16), 0, init_round_num, [])
    event = ReceivedConsensusDataEvent(data)
    event_system.simulator.raise_event(event)

    await start_event_system(event_system)
    assert not_data is async_layer._data_dict[init_round_num][not_data.id]
    assert data is async_layer._data_dict[init_round_num][data.id]


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num, init_round_num", parameters)
async def test_async_layer_not_data_later(async_layer_items,
                                          voter_num: int,
                                          init_round_num: int):
    node_id, event_system, async_layer, voters, data_factory, vote_factories = async_layer_items

    data = await data_factory.create_data(0, os.urandom(16), 0, init_round_num, [])
    event = ReceivedConsensusDataEvent(data)
    event_system.simulator.raise_event(event)

    await start_event_system(event_system)
    assert data is async_layer._data_dict[init_round_num][data.id]

    not_data = await data_factory.create_not_data(0, 0, init_round_num, voters[0])
    event = ReceivedConsensusDataEvent(not_data)
    event_system.simulator.raise_event(event)

    await start_event_system(event_system)
    assert not_data.id not in async_layer._data_dict[init_round_num]


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num, init_round_num", parameters)
async def test_async_layer_not_vote_early(async_layer_items,
                                          voter_num: int,
                                          init_round_num: int):
    node_id, event_system, async_layer, voters, data_factory, vote_factories = async_layer_items

    for voter, vote_factory in zip(voters, vote_factories):
        vote_factory = cast(DefaultConsensusVoteFactory, vote_factory)
        not_vote = await vote_factory.create_not_vote(voter, 0, init_round_num)
        event = ReceivedConsensusVoteEvent(not_vote)
        event_system.simulator.raise_event(event)

        await start_event_system(event_system)
        assert not_vote is async_layer._vote_dict[init_round_num][voter][not_vote.id]

        vote = await vote_factory.create_vote(os.urandom(16), b'', 0, init_round_num)
        event = ReceivedConsensusVoteEvent(vote)
        event_system.simulator.raise_event(event)

        await start_event_system(event_system)
        assert not_vote is async_layer._vote_dict[init_round_num][voter][not_vote.id]
        assert vote is async_layer._vote_dict[init_round_num][voter][vote.id]


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num, init_round_num", parameters)
async def test_async_layer_not_vote_later(async_layer_items,
                                          voter_num: int,
                                          init_round_num: int):
    node_id, event_system, async_layer, voters, data_factory, vote_factories = async_layer_items

    for voter, vote_factory in zip(voters, vote_factories):
        vote_factory = cast(DefaultConsensusVoteFactory, vote_factory)
        vote = await vote_factory.create_vote(os.urandom(16), b'', 0, init_round_num)
        event = ReceivedConsensusVoteEvent(vote)
        event_system.simulator.raise_event(event)

        await start_event_system(event_system)
        assert vote is async_layer._vote_dict[init_round_num][voter][vote.id]

        not_vote = await vote_factory.create_not_vote(voter, 0, init_round_num)
        event = ReceivedConsensusVoteEvent(not_vote)
        event_system.simulator.raise_event(event)

        await start_event_system(event_system)
        assert vote is async_layer._vote_dict[init_round_num][voter][vote.id]
        assert not_vote.id is not async_layer._vote_dict[init_round_num][voter]

