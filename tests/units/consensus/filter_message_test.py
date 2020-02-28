from typing import List
from mock import MagicMock

import pytest

from lft.app.data import DefaultData
from lft.app.epoch import RotateEpoch
from lft.app.vote import DefaultVote
from lft.consensus.messages.data import DataPool
from lft.consensus.messages.vote import VotePool, VoteFactory
from tests.units.consensus.mocks import RoundMock
from tests.units.consensus.setup_consensus import setup_consensus

INVALID_ID = b'invalid'


@pytest.mark.asyncio
async def test_receive_invalid_proposer_data():
    # GIVEN
    consensus, voters, vote_factories, epoch, genesis_data = await setup_consensus()
    mocking_message_pool(consensus)

    # WHEN
    data = await create_valid_data(0, voters, vote_factories)
    data._proposer_id = voters[1]
    await consensus.receive_data(data)

    # THEN
    assert_not_added_any_message(consensus)


@pytest.mark.asyncio
async def test_receive_invalid_voter():
    # GIVEN
    consensus, voters, vote_factories, epoch, genesis_data = await setup_consensus()
    mocking_message_pool(consensus)

    # WHEN
    invalid_vote = DefaultVote(
        id_=INVALID_ID,
        data_id=b'data',
        commit_id=genesis_data.id,
        voter_id=b'Im not voter',
        epoch_num=1,
        round_num=0
    )
    await consensus.receive_vote(invalid_vote)

    assert_not_added_any_message(consensus)


@pytest.mark.asyncio
async def test_receive_invalid_prev_voter():
    # GIVEN
    consensus, voters, vote_factories, epoch, genesis_data = await setup_consensus()
    mocking_message_pool(consensus)

    invalid_vote = DefaultVote(
        id_=INVALID_ID,
        data_id=b'data',
        commit_id=genesis_data.id,
        voter_id=b'Im not voter',
        epoch_num=1,
        round_num=0
    )

    # WHEN
    invalid_proposer_data = DefaultData(
        id_=INVALID_ID,
        prev_id=genesis_data.id,
        proposer_id=voters[0],
        number=1,
        epoch_num=1,
        round_num=0,
        prev_votes=[invalid_vote]
    )
    await consensus.receive_data(invalid_proposer_data)

    # THEN
    consensus._vote_pool.add_vote.assert_not_called()


@pytest.mark.skip("It will be resolved on next ticket")
@pytest.mark.asyncio
async def test_receive_past_round_message():
    # GIVEN
    consensus, voters, vote_factories, epoch, genesis_data = await setup_consensus()
    mocking_message_pool(consensus)

    candidate_round = RoundMock(epoch, 4)
    consensus._round_pool.first_round = MagicMock(return_value=candidate_round)

    # WHEN
    data = await create_valid_data(3, voters, vote_factories)
    await consensus.receive_data(data)
    past_vote = DefaultVote(
        id_=b'id',
        data_id=b'id',
        commit_id=b"prev",
        voter_id=voters[1],
        epoch_num=1,
        round_num=3
    )
    await consensus.receive_vote(past_vote)

    # THEN
    assert_not_added_any_message(consensus)


@pytest.mark.asyncio
async def test_receive_past_epoch():
    # GIVEN
    consensus, voters, vote_factories, epoch, genesis_data = await setup_consensus()
    mocking_message_pool(consensus)

    consensus._epoch_pool.add_epoch(RotateEpoch(2, voters))
    consensus._epoch_pool.prune_epoch(2)

    # WHEN
    prev_votes = [await vote_factory.create_vote(b'prev', b'commit', 1, 2) for vote_factory in vote_factories]

    past_data = DefaultData(
        id_=b'id',
        prev_id=b'prev',
        number=3,
        proposer_id=voters[3],
        epoch_num=1,
        round_num=3,
        prev_votes=prev_votes
    )

    await consensus.receive_data(past_data)
    past_vote = DefaultVote(
        id_=b'id',
        data_id=b'id',
        commit_id=b"prev",
        voter_id=voters[1],
        epoch_num=1,
        round_num=3
    )
    await consensus.receive_vote(past_vote)

    # THEN
    assert_not_added_any_message(consensus)


@pytest.mark.asyncio
async def test_receive_future_epoch():
    # GIVEN
    consensus, voters, vote_factories, epoch, genesis_data = await setup_consensus()
    mocking_message_pool(consensus)

    # WHEN
    prev_votes = [await vote_factory.create_vote(b'prev', b'commit', 2, 0) for vote_factory in vote_factories]
    past_data = DefaultData(
        id_=b'id',
        prev_id=b'prev',
        number=3,
        proposer_id=voters[3],
        epoch_num=2,
        round_num=1,
        prev_votes=prev_votes
    )
    await consensus.receive_data(past_data)
    past_vote = DefaultVote(
        id_=b'id',
        data_id=b'id',
        commit_id=b"prev",
        voter_id=voters[1],
        epoch_num=2,
        round_num=1
    )
    await consensus.receive_vote(past_vote)

    # THEN
    assert_not_added_any_message(consensus)


def assert_not_added_any_message(consensus):
    consensus._data_pool.add_data.assert_not_called()
    print("add data is not called")
    consensus._vote_pool.add_vote.assert_not_called()


def mocking_message_pool(consensus):
    consensus._data_pool = MagicMock(DataPool())
    consensus._vote_pool = MagicMock(VotePool())


async def create_valid_data(round_: int, voters, vote_factories: List[VoteFactory]):
    if round_ == 0:
        prev_votes = []
    else:
        prev_votes = [await vote_factory.create_vote(b'prev', b'commit', 1, round_) for vote_factory in vote_factories]

    return DefaultData(
        id_=b'data',
        prev_id=b'prev',
        proposer_id=voters[round_ % 4],
        number=round_ + 1,
        epoch_num=1,
        round_num=round_,
        prev_votes=prev_votes
    )
