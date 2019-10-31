import os
from contextlib import asynccontextmanager
from unittest.mock import MagicMock
from lft.app.data import DefaultDataFactory
from lft.app.vote import DefaultVoteFactory
from lft.app.term import RotateTermFactory, RotateTerm
from lft.consensus.layers.sync_layer import SyncLayer
from lft.consensus.layers.round_layer import RoundLayer
from lft.event import EventSystem


@asynccontextmanager
async def setup_items(voter_num: int, round_num: int):
    voters = [os.urandom(16) for _ in range(voter_num)]
    voter = voters[0]

    event_system = MagicMock(EventSystem(use_priority=True))

    data_factory = DefaultDataFactory(voter)
    vote_factory = DefaultVoteFactory(voter)
    term_factor = RotateTermFactory(1)

    round_layer = MagicMock(RoundLayer(voter, event_system, data_factory, vote_factory))
    sync_layer = SyncLayer(round_layer,
                           voter,
                           event_system,
                           data_factory,
                           vote_factory)

    try:
        genesis_data = await data_factory.create_data(0, b'', 0, round_num, [])
        term = RotateTerm(0, voters)
        await sync_layer.initialize(term, round_num, genesis_data, [])

        yield voters, event_system, sync_layer, round_layer, genesis_data
    finally:
        sync_layer.close()
