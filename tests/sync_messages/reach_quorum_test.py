import os
import random
import pytest
from typing import Tuple, Sequence
from lft.app.vote import DefaultVoteFactory, DefaultVote
from lft.consensus.layers.sync import SyncMessages


@pytest.fixture
async def setup(voter_num: int):
    voters = [os.urandom(16) for _ in range(voter_num)]
    vote_factories = [DefaultVoteFactory(voter) for voter in voters]
    random.shuffle(vote_factories)

    quorum = random.randint(2, len(vote_factories))
    return voters, vote_factories, quorum, SyncMessages()


Setup = Tuple[Sequence[bytes], Sequence[DefaultVoteFactory], int, SyncMessages]


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num", range(4, 100))
async def test_reach_quorum(setup: Setup, voter_num: int):
    voters, vote_factories, quorum, sync_messages = setup

    for vote_factory in vote_factories[:quorum - 1]:
        vote = await vote_factory.create_vote(data_id=os.urandom(16),
                                              commit_id=os.urandom(16),
                                              term_num=random.randint(0, 10),
                                              round_num=random.randint(0, 10))
        sync_messages.add_vote(vote)

    assert not sync_messages.reach_quorum(quorum)

    vote_factory = vote_factories[-1]
    vote = await vote_factory.create_vote(data_id=os.urandom(16),
                                          commit_id=os.urandom(16),
                                          term_num=random.randint(0, 10),
                                          round_num=random.randint(0, 10))
    sync_messages.add_vote(vote)

    assert sync_messages.reach_quorum(quorum)
    assert not sync_messages.reach_quorum_consensus(quorum)


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num", range(4, 100))
async def test_reach_quorum_duplicate(setup: Setup, voter_num: int):
    voters, vote_factories, quorum, sync_messages = setup

    for vote_factory in vote_factories[:quorum - 1]:
        # duplicate votes for same data.
        # The votes have different vote ID.
        for _ in range(random.randint(2, quorum)):
            vote = DefaultVote(id_=os.urandom(16),
                               data_id=os.urandom(16),
                               commit_id=os.urandom(16),
                               voter_id=vote_factory._node_id,
                               term_num=random.randint(0, 10),
                               round_num=random.randint(0, 10))
            sync_messages.add_vote(vote)

    assert not sync_messages.reach_quorum(quorum)

    vote_factory = vote_factories[-1]
    vote = await vote_factory.create_vote(data_id=os.urandom(16),
                                          commit_id=os.urandom(16),
                                          term_num=random.randint(0, 10),
                                          round_num=random.randint(0, 10))
    sync_messages.add_vote(vote)

    assert sync_messages.reach_quorum(quorum)
    assert not sync_messages.reach_quorum_consensus(quorum)


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num", range(4, 100))
async def test_reach_quorum_none_vote(setup: Setup, voter_num: int):
    voters, vote_factories, quorum, sync_messages = setup

    for vote_factory in vote_factories[:quorum - 1]:
        vote = await vote_factory.create_none_vote(term_num=random.randint(0, 10), round_num=random.randint(0, 10))
        sync_messages.add_vote(vote)

    assert not sync_messages.reach_quorum(quorum)

    vote_factory = vote_factories[-1]
    vote = await vote_factory.create_none_vote(term_num=random.randint(0, 10), round_num=random.randint(0, 10))
    sync_messages.add_vote(vote)

    assert sync_messages.reach_quorum(quorum)


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num", range(4, 100))
async def test_reach_quorum_integration(setup: Setup, voter_num: int):
    voters, vote_factories, quorum, sync_messages = setup

    for vote_factory in vote_factories[:quorum - 1]:
        for _ in range(random.randint(2, quorum)):
            vote = await _random_vote(vote_factory)
            sync_messages.add_vote(vote)

    assert not sync_messages.reach_quorum(quorum)

    vote_factory = vote_factories[-1]
    vote = await _random_vote(vote_factory)
    sync_messages.add_vote(vote)

    assert sync_messages.reach_quorum(quorum)


async def _random_vote(vote_factory: DefaultVoteFactory):
    r = random.randint(0, 15)
    if r < 5:
        return DefaultVote(id_=os.urandom(16),
                           data_id=os.urandom(16),
                           commit_id=os.urandom(16),
                           voter_id=vote_factory._node_id,
                           term_num=random.randint(0, 10),
                           round_num=random.randint(0, 10))
    elif r < 10:
        return await vote_factory.create_lazy_vote(voter_id=vote_factory._node_id,
                                                   term_num=random.randint(0, 10),
                                                   round_num=random.randint(0, 10))
    else:
        return await vote_factory.create_none_vote(term_num=random.randint(0, 10),
                                                   round_num=random.randint(0, 10))
