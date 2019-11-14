import os
import random
import pytest
from typing import Tuple, Sequence
from lft.app.data import DefaultDataFactory, DefaultData
from lft.app.vote import DefaultVoteFactory, DefaultVote
from lft.consensus.layers.sync import SyncMessages


@pytest.fixture
async def setup(voter_num: int):
    voters = [os.urandom(16) for _ in range(voter_num)]
    vote_factories = [DefaultVoteFactory(voter) for voter in voters]
    random.shuffle(vote_factories)

    data_factory = DefaultDataFactory(voters[0])
    data = await data_factory.create_data(data_number=0,
                                          prev_id=os.urandom(16),
                                          term_num=0,
                                          round_num=0,
                                          prev_votes=())
    quorum = random.randint(1, len(vote_factories))
    return voters, vote_factories, quorum, data, SyncMessages()


Setup = Tuple[Sequence[bytes], Sequence[DefaultVoteFactory], int, DefaultData, SyncMessages]


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num", range(4, 100))
async def test_reach_quorum_consensus(setup: Setup, voter_num: int):
    voters, vote_factories, quorum, data, sync_messages = setup

    for vote_factory in vote_factories[:quorum - 1]:
        vote = await vote_factory.create_vote(data.id, data.prev_id, data.term_num, data.round_num)
        sync_messages.add_vote(vote)

    assert not sync_messages.reach_quorum_consensus(quorum)

    vote_factory = vote_factories[-1]
    vote = await vote_factory.create_vote(data.id, data.prev_id, data.term_num, data.round_num)
    sync_messages.add_vote(vote)

    assert sync_messages.reach_quorum_consensus(quorum)


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num", range(4, 100))
async def test_reach_quorum_consensus_duplicate(setup: Setup, voter_num: int):
    voters, vote_factories, quorum, data, sync_messages = setup

    for vote_factory in vote_factories[:quorum - 1]:
        # duplicate votes for same data.
        # The votes have different vote ID.
        for _ in range(random.randint(2, quorum)):
            vote = DefaultVote(
                os.urandom(16), data.id, data.prev_id, vote_factory._node_id, data.term_num,data.round_num
            )
            sync_messages.add_vote(vote)

    assert not sync_messages.reach_quorum_consensus(quorum)

    vote_factory = vote_factories[-1]
    vote = await vote_factory.create_vote(data.id, data.prev_id, data.term_num, data.round_num)
    sync_messages.add_vote(vote)

    assert sync_messages.reach_quorum_consensus(quorum)


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num", range(4, 100))
async def test_reach_quorum_consensus_none_vote(setup: Setup, voter_num: int):
    voters, vote_factories, quorum, data, sync_messages = setup

    for vote_factory in vote_factories[:quorum - 1]:
        vote = await vote_factory.create_none_vote(data.term_num, data.round_num)
        sync_messages.add_vote(vote)

    assert not sync_messages.reach_quorum_consensus(quorum)

    vote_factory = vote_factories[-1]
    vote = await vote_factory.create_none_vote(data.term_num, data.round_num)
    sync_messages.add_vote(vote)

    assert sync_messages.reach_quorum_consensus(quorum)
