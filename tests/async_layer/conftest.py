import os
import pytest
from lft.consensus.default_data.factories import DefaultConsensusDataFactory, DefaultConsensusVoteFactory
from lft.consensus.events import InitializeEvent
from lft.consensus.layers.async_.async_layer import AsyncLayer
from lft.event import EventSystem
from lft.event.mediators import DelayedEventMediator


@pytest.fixture(scope="function")
def async_layer_items(voter_num: int):
    node_id = os.urandom(16)
    event_system = EventSystem()
    event_system.set_mediator(DelayedEventMediator)
    async_layer = AsyncLayer(node_id,
                             event_system,
                             DefaultConsensusDataFactory(node_id),
                             DefaultConsensusVoteFactory(node_id))
    voters = [os.urandom(16) for _ in range(voter_num - 1)]
    voters.insert(0, node_id)

    data_factory = DefaultConsensusDataFactory(node_id)
    voters_factories = [DefaultConsensusVoteFactory(voter) for voter in voters]

    event = InitializeEvent(0, 0, None, voters)
    event_system.simulator.raise_event(event)

    return node_id, event_system, async_layer, voters, data_factory, voters_factories

