import os
from contextlib import asynccontextmanager
from mock import MagicMock
from lft.app.data import DefaultDataFactory
from lft.app.vote import DefaultVoteFactory
from lft.app.epoch import RotateEpoch
from lft.consensus.election import Election
from lft.consensus.round import Round
from lft.consensus.messages.data import DataPool
from lft.consensus.messages.vote import VotePool
from lft.event import EventSystem


@asynccontextmanager
async def setup_items(voter_num: int, round_num: int):
    voters = [os.urandom(16) for _ in range(voter_num)]
    voter = voters[0]

    epoch = RotateEpoch(1, voters)
    event_system = MagicMock(EventSystem(use_priority=True))

    data_factory = DefaultDataFactory(voter)
    vote_factory = DefaultVoteFactory(voter)

    election = MagicMock(Election(voter,
                                  epoch,
                                  round_num,
                                  event_system,
                                  data_factory,
                                  vote_factory,
                                  DataPool(),
                                  VotePool()))
    round_ = Round(election,
                   voter,
                   epoch,
                   round_num,
                   event_system,
                   data_factory,
                   vote_factory)

    try:
        genesis_epoch_num = 0
        genesis_round_num = 0
        genesis_data = await data_factory.create_data(0, b'', genesis_epoch_num, genesis_round_num, ())
        genesis_votes = ()

        candidate_data = genesis_data
        candidate_votes = genesis_votes
        yield voters, event_system, round_, election, epoch, candidate_data, candidate_votes
    finally:
        pass
