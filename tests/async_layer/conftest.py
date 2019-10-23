import os
import pytest
from functools import partial
from lft.app.data import DefaultDataFactory
from lft.app.vote import DefaultVoteFactory
from lft.app.term import RotateTermFactory
from lft.consensus.events import InitializeEvent
from lft.consensus.layers.async_.async_layer import AsyncLayer
from lft.consensus.layers.sync.sync_layer import SyncLayer
from lft.event import EventSystem, Event
from lft.event.mediators import DelayedEventMediator


@pytest.fixture(scope="function")
def async_layer_items(init_round_num: int, voter_num: int):
    node_id = os.urandom(16)
    event_system = EventSystem()
    event_system.set_mediator(DelayedEventMediator)

    data_factory = DefaultDataFactory(node_id)
    vote_factory = DefaultVoteFactory(node_id)
    term_factor = RotateTermFactory(1)
    async_layer = AsyncLayer(SyncLayer(node_id, event_system, data_factory, vote_factory, term_factor),
                             node_id,
                             event_system,
                             data_factory,
                             vote_factory,
                             term_factor)
    voters = [os.urandom(16) for _ in range(voter_num - 1)]
    voters.insert(0, node_id)

    data_factory = DefaultDataFactory(node_id)
    voters_factories = [DefaultVoteFactory(voter) for voter in voters]

    event = InitializeEvent(0, init_round_num, None, None, voters)
    event_system.simulator.raise_event(event)

    return node_id, event_system, async_layer, voters, data_factory, voters_factories


async def start_event_system(event_system: EventSystem):
    event = _StopEvent()
    event.deterministic = False
    event_system.simulator.raise_event(event)
    event_system.simulator.register_handler(_StopEvent, partial(_stop, event_system))

    await event_system.start(blocking=False)


class _StopEvent(Event):
    pass


def _stop(event_system: EventSystem, event: _StopEvent):
    event_system.stop()

