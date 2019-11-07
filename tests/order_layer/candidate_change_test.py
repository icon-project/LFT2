import pytest

from lft.app.data import DefaultData
from lft.app.term import RotateTerm
from lft.app.vote import DefaultVoteFactory
from lft.consensus.events import ReceivedDataEvent, StartRoundEvent
from tests.order_layer.setup_order_layer import setup_order_layer


@pytest.mark.asyncio
async def test_change_by_data():
    # GIVEN
    order_layer, sync_layer, voters, event_system = await setup_order_layer()
    change_candidate_data = DefaultData(
        id_=b'first',
        prev_id=b'genesis',
        proposer_id=voters[1],
        number=1,
        term_num=0,
        round_num=1,
        prev_votes=[]
    )
    await order_layer._on_event_received_data(
        ReceivedDataEvent(change_candidate_data)
    )
    await order_layer._on_event_start_round(
        StartRoundEvent(
            term=RotateTerm(0, voters),
            round_num=2
        )
    )

    # WHEN
    vote_factories = []
    for voter in voters:
        vote_factories.append(DefaultVoteFactory(voter))

    prev_votes = [await vote_factory.create_vote(b'first', b'genesis', 0, 1)
                  for vote_factory in vote_factories]

    await order_layer._on_event_received_data(
        ReceivedDataEvent(
            DefaultData(
                id_=b'second',
                prev_id=b'first',
                proposer_id=voters[2],
                number=2,
                term_num=0,
                round_num=2,
                prev_votes=prev_votes
            )
        )
    )

    # THEN
    assert len(sync_layer.initialize.call_args_list) == 2

    init_params = sync_layer.initialize.call_args_list[1][0]
    assert init_params[0] == RotateTerm(0, voters)
    assert init_params[1] == 2
    assert init_params[2] == change_candidate_data
    assert init_params[3] == prev_votes



@pytest.mark.asyncio
async def test_change_by_vote():
    order_layer, sync_layer, voters, event_system = await setup_order_layer()


@pytest.mark.asyncio
async def test_change_by_data_with_missing_data():
    # GIVEN
    order_layer, sync_layer, voters, event_system = await setup_order_layer()


@pytest.mark.asyncio
async def test_change_by_vote_with_missing_data():
    order_layer, sync_layer, voters, event_system = await setup_order_layer()
