import pytest

from lft.app.vote import DefaultVote
from lft.consensus.events import ReceivedVoteEvent
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
    order_layer._on_event_received_vote(ReceivedVoteEvent(vote))
    # THEN
    sync_layer.receive_vote.assert_called_once_with(vote)
