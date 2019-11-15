import pytest

from lft.app.vote import DefaultVote
from lft.consensus.events import ReceiveVoteEvent
from tests.order_layer.setup_order_layer import setup_order_layer


@pytest.mark.asyncio
async def test_receive_now_round_vote():
    # GIVEN
    order_layer, sync_layer, voters, event_system = await setup_order_layer()
    vote = DefaultVote(
        id_=b'vote_id',
        data_id=b'data_id',
        commit_id=b'genesis',
        voter_id=voters[0],
        term_num=0,
        round_num=1
    )
    # WHEN
    await order_layer._on_event_receive_vote(ReceiveVoteEvent(vote))
    # THEN
    sync_layer.receive_vote.assert_called_once_with(vote)


@pytest.mark.asyncio
async def test_receive_past_vote():
    # GIVEN
    order_layer, sync_layer, voters, event_system = await setup_order_layer()
    vote = DefaultVote(
        id_=b'vote_id',
        data_id=b'data_id',
        commit_id=b'genesis',
        voter_id=voters[0],
        term_num=0,
        round_num=0
    )
    # WHEN
    await order_layer._on_event_receive_vote(ReceiveVoteEvent(vote))
    # THEN
    sync_layer.receive_vote.assert_not_called()


@pytest.mark.asyncio
async def test_receive_future_vote():
    # GIVEN
    order_layer, sync_layer, voters, event_system = await setup_order_layer()
    vote = DefaultVote(
        id_=b'vote_id',
        data_id=b'data_id',
        commit_id=b'genesis',
        voter_id=voters[2],
        term_num=0,
        round_num=10
    )
    # WHEN
    await order_layer._on_event_receive_vote(ReceiveVoteEvent(vote))
    # THEN
    votes = order_layer._get_votes(0, 10)
    assert len(votes) == 1
    assert next(iter(votes)) == vote


@pytest.mark.asyncio
async def test_receive_invalid_term_vote():
    # GIVEN
    order_layer, sync_layer, voters, event_system = await setup_order_layer()
    vote = DefaultVote(
        id_=b'vote_id',
        data_id=b'data_id',
        commit_id=b'genesis',
        voter_id=voters[0],
        term_num=1,
        round_num=0
    )
    # WHEN
    await order_layer._on_event_receive_vote(ReceiveVoteEvent(vote))
    # THEN
    sync_layer.receive_vote.assert_not_called()
    assert len(order_layer._get_votes(1, 0)) == 0


@pytest.mark.asyncio
async def test_receive_invalid_voter_vote():
    # GIVEN
    order_layer, sync_layer, voters, event_system = await setup_order_layer()
    vote = DefaultVote(
        id_=b'vote_id',
        data_id=b'data_id',
        commit_id=b'genesis',
        voter_id=b'invalid_voter',
        term_num=0,
        round_num=1
    )
    # WHEN
    await order_layer._on_event_receive_vote(ReceiveVoteEvent(vote))
    # THEN
    sync_layer.receive_vote.assert_not_called()
    assert len(order_layer._get_votes(0, 1)) == 0
