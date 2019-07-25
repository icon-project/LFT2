import os
import pytest
from functools import partial
from lft.consensus.events import ReceivedConsensusDataEvent, ReceivedConsensusVoteEvent
from lft.event import EventSystem, Event


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num", list(i for i in range(4, 100)))
async def test_async_layer_basic(async_layer_items, voter_num: int):
    node_id, event_system, async_layer, voters, data_factory, vote_factories = async_layer_items

    data = await data_factory.create_data(0, os.urandom(16), 0, 0)
    event = ReceivedConsensusDataEvent(data)
    event_system.simulator.raise_event(event)

    votes = []
    for voter, vote_factory in zip(voters[1:], vote_factories[1:]):
        vote = await vote_factory.create_vote(data.id, data.term_num, data.round_num)
        votes.append(vote)
        event = ReceivedConsensusVoteEvent(vote)
        event.deterministic = False
        event_system.simulator.raise_event(event)

    event = _StopEvent()
    event.deterministic = False
    event_system.simulator.raise_event(event)
    event_system.simulator.register_handler(_StopEvent, partial(_stop, event_system))

    await event_system.start(blocking=False)

    assert data is async_layer._data_dict[0][data.id]
    assert len(async_layer._data_dict) == 1
    assert len(async_layer._data_dict[0]) == 1

    for voter, vote in zip(voters[1:], votes):
        assert vote is async_layer._vote_dict[0][voter][vote.id]
        assert len(async_layer._vote_dict[0][voter]) == 1
    assert len(async_layer._vote_dict) == 1
    assert len(async_layer._vote_dict[0]) == voter_num - 1


class _StopEvent(Event):
    pass


def _stop(event_system: EventSystem, event: _StopEvent):
    event_system.stop()

