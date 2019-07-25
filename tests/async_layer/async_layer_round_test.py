import os
import random
import pytest
from typing import cast
from lft.consensus.events import ReceivedConsensusDataEvent, ReceivedConsensusVoteEvent
from lft.consensus.default_data.factories import DefaultConsensusVoteFactory
from .conftest import start_event_system

param_count = 10

voter_nums = [random.randint(4, 100) for _ in range(param_count)]
init_round_nums = [random.randint(1, 100) for _ in range(param_count)]
data_round_nums = [random.randint(0, init_round_num - 1) for init_round_num in init_round_nums]
parameters = list(zip(voter_nums, init_round_nums, data_round_nums))


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num, init_round_num, data_round_num", parameters)
async def test_async_layer_past_round_data(async_layer_items,
                                           voter_num: int,
                                           init_round_num: int,
                                           data_round_num: int):
    node_id, event_system, async_layer, voters, data_factory, vote_factories = async_layer_items

    data = await data_factory.create_data(0, os.urandom(16), 0, data_round_num)
    event = ReceivedConsensusDataEvent(data)
    event_system.simulator.raise_event(event)

    await start_event_system(event_system)
    assert len(async_layer._data_dict) == 0


vote_round_nums = [random.randint(0, init_round_num - 1) for init_round_num in init_round_nums]
parameters = list(zip(voter_nums, init_round_nums, vote_round_nums))


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num, init_round_num, vote_round_num", parameters)
async def test_async_layer_past_round_vote(async_layer_items,
                                           voter_num: int,
                                           init_round_num: int,
                                           vote_round_num: int):
    node_id, event_system, async_layer, voters, data_factory, vote_factories = async_layer_items

    for vote, vote_factory in zip(voters, vote_factories):
        vote_factory = cast(DefaultConsensusVoteFactory, vote_factory)
        vote = await vote_factory.create_vote(os.urandom(16), 0, vote_round_num)

        event = ReceivedConsensusVoteEvent(vote)
        event_system.simulator.raise_event(event)

    await start_event_system(event_system)
    assert len(async_layer._vote_dict) == 0


voter_nums = [random.randint(4, 100) for _ in range(param_count)]
init_round_nums = [random.randint(0, 100) for _ in range(param_count)]
data_round_nums = [random.randint(num + 1, num + 10) for num in init_round_nums]

parameters = list(zip(voter_nums, init_round_nums, data_round_nums))


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num, init_round_num, data_round_num", parameters)
async def test_async_layer_future_round_data(async_layer_items,
                                             voter_num: int,
                                             init_round_num: int,
                                             data_round_num: int):
    node_id, event_system, async_layer, voters, data_factory, vote_factories = async_layer_items

    data = await data_factory.create_data(0, os.urandom(16), 0, data_round_num)
    event = ReceivedConsensusDataEvent(data)
    event_system.simulator.raise_event(event)

    await start_event_system(event_system)
    assert len(async_layer._data_dict) == 1


vote_round_nums = [random.randint(num + 1, num + 10) for num in init_round_nums]
parameters = list(zip(voter_nums, init_round_nums, vote_round_nums))


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num, init_round_num, vote_round_num", parameters)
async def test_async_layer_future_round_vote(async_layer_items,
                                             voter_num: int,
                                             init_round_num: int,
                                             vote_round_num: int):
    node_id, event_system, async_layer, voters, data_factory, vote_factories = async_layer_items

    votes = []
    for vote, vote_factory in zip(voters, vote_factories):
        vote_factory = cast(DefaultConsensusVoteFactory, vote_factory)
        vote = await vote_factory.create_vote(os.urandom(16), 0, vote_round_num)
        votes.append(vote)

        event = ReceivedConsensusVoteEvent(vote)
        event_system.simulator.raise_event(event)

    await start_event_system(event_system)

    assert len(async_layer._vote_dict) == 1
    assert len(async_layer._vote_dict[vote_round_num]) == voter_num
    for voter, vote in zip(voters, votes):
        assert len(async_layer._vote_dict[vote_round_num][voter]) == 1
        assert vote is async_layer._vote_dict[vote_round_num][voter][vote.id]

