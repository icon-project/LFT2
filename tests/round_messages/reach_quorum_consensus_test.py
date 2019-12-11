import os
import random
import pytest
from typing import Tuple, Sequence
from lft.app.data import DefaultDataFactory, DefaultData
from lft.app.vote import DefaultVoteFactory, DefaultVote
from lft.consensus.round import RoundMessages


@pytest.fixture
async def setup(voter_num: int):
    voters = [os.urandom(16) for _ in range(voter_num)]
    vote_factories = [DefaultVoteFactory(voter) for voter in voters]
    random.shuffle(vote_factories)

    data_factory = DefaultDataFactory(voters[0])
    data = await data_factory.create_data(data_number=0,
                                          prev_id=os.urandom(16),
                                          epoch_num=0,
                                          round_num=0,
                                          prev_votes=())
    quorum = random.randint(1, len(vote_factories))
    return voters, vote_factories, quorum, data, RoundMessages()


Setup = Tuple[Sequence[bytes], Sequence[DefaultVoteFactory], int, DefaultData, RoundMessages]


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num", range(4, 100))
async def test_reach_quorum_consensus(setup: Setup, voter_num: int):
    voters, vote_factories, quorum, data, round_messages = setup

    for vote_factory in vote_factories[:quorum - 1]:
        vote = await vote_factory.create_vote(data.id, data.prev_id, data.epoch_num, data.round_num)
        round_messages.add_vote(vote)

    assert not round_messages.reach_quorum_consensus(quorum)

    vote_factory = vote_factories[-1]
    vote = await vote_factory.create_vote(data.id, data.prev_id, data.epoch_num, data.round_num)
    round_messages.add_vote(vote)

    assert round_messages.reach_quorum_consensus(quorum)


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num", range(4, 100))
async def test_reach_quorum_consensus_duplicate(setup: Setup, voter_num: int):
    voters, vote_factories, quorum, data, round_messages = setup

    for vote_factory in vote_factories[:quorum - 1]:
        # duplicate votes for same data.
        # The votes have different vote ID.
        for _ in range(random.randint(2, quorum)):
            vote = DefaultVote(
                os.urandom(16), data.id, data.prev_id, vote_factory._node_id, data.epoch_num,data.round_num
            )
            round_messages.add_vote(vote)

    assert not round_messages.reach_quorum_consensus(quorum)

    vote_factory = vote_factories[-1]
    vote = await vote_factory.create_vote(data.id, data.prev_id, data.epoch_num, data.round_num)
    round_messages.add_vote(vote)

    assert round_messages.reach_quorum_consensus(quorum)


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num", range(4, 100))
async def test_reach_quorum_consensus_none_vote(setup: Setup, voter_num: int):
    voters, vote_factories, quorum, data, round_messages = setup

    for vote_factory in vote_factories[:quorum - 1]:
        vote = vote_factory.create_none_vote(data.epoch_num, data.round_num)
        round_messages.add_vote(vote)

    assert not round_messages.reach_quorum_consensus(quorum)

    vote_factory = vote_factories[-1]
    vote = vote_factory.create_none_vote(data.epoch_num, data.round_num)
    round_messages.add_vote(vote)

    assert round_messages.reach_quorum_consensus(quorum)
