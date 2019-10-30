import os
import pytest
from asyncio import QueueEmpty
from lft.app.data import DefaultDataFactory
from lft.app.vote import DefaultVoteFactory
from lft.app.term import RotateTermFactory
from lft.consensus.layers.sync_layer import SyncLayer
from lft.consensus.layers.round_layer import RoundLayer
from lft.event import EventSystem
from lft.event.mediators import DelayedEventMediator


async def setup_sync_layers(voter_num: int):
    voters = [os.urandom(16) for _ in range(voter_num)]
    sync_layers = []
    event_systems = []
    data_factories = []
    vote_factories = []
    for voter in voters:
        event_system = EventSystem()
        event_system.set_mediator(DelayedEventMediator)
        event_system.start(blocking=False)

        data_factory = DefaultDataFactory(voter)
        vote_factory = DefaultVoteFactory(voter)
        term_factor = RotateTermFactory(1)
        sync_layer = SyncLayer(RoundLayer(voter, event_system, data_factory, vote_factory, term_factor),
                               voter,
                               event_system,
                               data_factory,
                               vote_factory,
                               term_factor)

        sync_layers.append(sync_layer)
        event_systems.append(event_system)
        data_factories.append(data_factory)
        vote_factories.append(vote_factory)

    return voters, event_systems, sync_layers, data_factories, vote_factories


def get_event(event_system: EventSystem):
    _, _, event = event_system.simulator._event_tasks.get_nowait()
    return event


def verify_no_events(event_system):
    with pytest.raises(QueueEmpty):
        event = get_event(event_system)
        print("remain event: " + event)
