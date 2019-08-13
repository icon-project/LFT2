import os
import random
import pytest

from lft.app.data import DefaultConsensusDataFactory
from lft.consensus.events import ReceivedConsensusDataEvent, ReceivedConsensusVoteEvent
from lft.consensus.term import RotateTerm
from .conftest import start_event_system


param_count = 10

voter_nums = [random.randint(4, 20) for _ in range(param_count)]
init_round_nums = [random.randint(1, 100) for _ in range(param_count)]
data_counts = [random.randint(10, 20) for _ in range(param_count)]
parameters = list(zip(voter_nums, init_round_nums, data_counts))


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num, init_round_num, data_count", parameters)
async def test_async_layer_past_duplicate_data(async_layer_items,
                                               voter_num: int,
                                               init_round_num: int,
                                               data_count: int):
    node_id, event_system, async_layer, voters, data_factory, vote_factories = async_layer_items

    term = RotateTerm(0, voters)
    proposer = term.get_proposer_id(init_round_num)
    proposer_data_factory = DefaultConsensusDataFactory(proposer)

    for _ in range(data_count):
        data = await proposer_data_factory.create_data(0, os.urandom(16), 0, init_round_num)
        event = ReceivedConsensusDataEvent(data)
        for _ in range(data_count):
            event_system.simulator.raise_event(event)

    await start_event_system(event_system)
    assert len(async_layer._data_dict) == 1
    assert len(async_layer._data_dict[init_round_num]) == data_count


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num, init_round_num, vote_count", parameters)
async def test_async_layer_past_duplicate_vote(async_layer_items,
                                               voter_num: int,
                                               init_round_num: int,
                                               vote_count: int):
    node_id, event_system, async_layer, voters, data_factory, vote_factories = async_layer_items

    for _ in range(vote_count):
        for vote_factory in vote_factories:
            vote = await vote_factory.create_vote(os.urandom(16), b'', 0, init_round_num)
            event = ReceivedConsensusVoteEvent(vote)
            for _ in range(vote_count):
                event_system.simulator.raise_event(event)

    await start_event_system(event_system)
    assert len(async_layer._vote_dict) == 1
    assert len(async_layer._vote_dict[init_round_num]) == voter_num
    for vote_values in async_layer._vote_dict[init_round_num].values():
        vote_values = list(vote_values)
        assert len(vote_values) == vote_count

