import os
import random
import pytest
from typing import Tuple, Sequence
from lft.app.vote import DefaultVoteFactory, DefaultVote
from lft.consensus.round import RoundMessages


@pytest.fixture
async def setup(voter_num: int):
    voters = [os.urandom(16) for _ in range(voter_num)]
    vote_factories = [DefaultVoteFactory(voter) for voter in voters]
    random.shuffle(vote_factories)

    quorum = random.randint(2, len(vote_factories))
    return voters, vote_factories, quorum, RoundMessages()


Setup = Tuple[Sequence[bytes], Sequence[DefaultVoteFactory], int, RoundMessages]


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num", range(4, 100))
async def test_reach_quorum(setup: Setup, voter_num: int):
    voters, vote_factories, quorum, round_messages = setup

    for vote_factory in vote_factories[:quorum - 1]:
        vote = await vote_factory.create_vote(data_id=os.urandom(16),
                                              commit_id=os.urandom(16),
                                              epoch_num=random.randint(0, 10),
                                              round_num=random.randint(0, 10))
        round_messages.add_vote(vote)

    assert not round_messages.reach_quorum(quorum)

    vote_factory = vote_factories[-1]
    vote = await vote_factory.create_vote(data_id=os.urandom(16),
                                          commit_id=os.urandom(16),
                                          epoch_num=random.randint(0, 10),
                                          round_num=random.randint(0, 10))
    round_messages.add_vote(vote)

    assert round_messages.reach_quorum(quorum)
    assert not round_messages.reach_quorum_consensus(quorum)


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num", range(4, 100))
async def test_reach_quorum_duplicate(setup: Setup, voter_num: int):
    voters, vote_factories, quorum, round_messages = setup

    for vote_factory in vote_factories[:quorum - 1]:
        # duplicate votes for same data.
        # The votes have different vote ID.
        for _ in range(random.randint(2, quorum)):
            vote = DefaultVote(id_=os.urandom(16),
                               data_id=os.urandom(16),
                               commit_id=os.urandom(16),
                               voter_id=vote_factory._node_id,
                               epoch_num=random.randint(0, 10),
                               round_num=random.randint(0, 10))
            round_messages.add_vote(vote)

    assert not round_messages.reach_quorum(quorum)

    vote_factory = vote_factories[-1]
    vote = await vote_factory.create_vote(data_id=os.urandom(16),
                                          commit_id=os.urandom(16),
                                          epoch_num=random.randint(0, 10),
                                          round_num=random.randint(0, 10))
    round_messages.add_vote(vote)

    assert round_messages.reach_quorum(quorum)
    assert not round_messages.reach_quorum_consensus(quorum)


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num", range(4, 100))
async def test_reach_quorum_none_vote(setup: Setup, voter_num: int):
    voters, vote_factories, quorum, round_messages = setup

    for vote_factory in vote_factories[:quorum - 1]:
        vote = await vote_factory.create_none_vote(epoch_num=random.randint(0, 10), round_num=random.randint(0, 10))
        round_messages.add_vote(vote)

    assert not round_messages.reach_quorum(quorum)

    vote_factory = vote_factories[-1]
    vote = await vote_factory.create_none_vote(epoch_num=random.randint(0, 10), round_num=random.randint(0, 10))
    round_messages.add_vote(vote)

    assert round_messages.reach_quorum(quorum)


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num", range(4, 100))
async def test_reach_quorum_integration(setup: Setup, voter_num: int):
    voters, vote_factories, quorum, round_messages = setup

    for vote_factory in vote_factories[:quorum - 1]:
        for _ in range(random.randint(2, quorum)):
            vote = await _random_vote(vote_factory)
            round_messages.add_vote(vote)

    assert not round_messages.reach_quorum(quorum)

    vote_factory = vote_factories[-1]
    vote = await _random_vote(vote_factory)
    round_messages.add_vote(vote)

    assert round_messages.reach_quorum(quorum)


async def _random_vote(vote_factory: DefaultVoteFactory):
    r = random.randint(0, 15)
    if r < 5:
        return DefaultVote(id_=os.urandom(16),
                           data_id=os.urandom(16),
                           commit_id=os.urandom(16),
                           voter_id=vote_factory._node_id,
                           epoch_num=random.randint(0, 10),
                           round_num=random.randint(0, 10))
    elif r < 10:
        return await vote_factory.create_lazy_vote(voter_id=vote_factory._node_id,
                                                   epoch_num=random.randint(0, 10),
                                                   round_num=random.randint(0, 10))
    else:
        return await vote_factory.create_none_vote(epoch_num=random.randint(0, 10),
                                                   round_num=random.randint(0, 10))
