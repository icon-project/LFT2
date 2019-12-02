import os
from contextlib import asynccontextmanager
from unittest.mock import MagicMock
from lft.app.data import DefaultDataFactory
from lft.app.vote import DefaultVoteFactory
from lft.app.term import RotateTerm
from lft.consensus.layers.sync import SyncLayer
from lft.consensus.layers.round import RoundLayer
from lft.consensus.messages.data import DataPool
from lft.consensus.messages.vote import VotePool
from lft.event import EventSystem


@asynccontextmanager
async def setup_items(voter_num: int, round_num: int):
    voters = [os.urandom(16) for _ in range(voter_num)]
    voter = voters[0]

    term = RotateTerm(1, voters)
    event_system = MagicMock(EventSystem(use_priority=True))

    data_factory = DefaultDataFactory(voter)
    vote_factory = DefaultVoteFactory(voter)

    round_layer = MagicMock(RoundLayer(voter,
                                       term,
                                       round_num,
                                       event_system,
                                       data_factory,
                                       vote_factory,
                                       DataPool(),
                                       VotePool()))
    sync_layer = SyncLayer(round_layer,
                           voter,
                           term,
                           round_num,
                           event_system,
                           data_factory,
                           vote_factory)

    try:
        genesis_term_num = 0
        genesis_round_num = 0
        genesis_data = await data_factory.create_data(0, b'', genesis_term_num, genesis_round_num, ())
        genesis_votes = ()

        candidate_data = genesis_data
        candidate_votes = genesis_votes
        yield voters, event_system, sync_layer, round_layer, term, candidate_data, candidate_votes
    finally:
        pass
