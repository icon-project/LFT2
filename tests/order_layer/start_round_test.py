import pytest

from lft.app.data import DefaultData
from lft.app.term import RotateTerm
from lft.app.vote import DefaultVote
from lft.consensus.events import ReceivedDataEvent, ReceivedVoteEvent, StartRoundEvent
from lft.consensus.term import Term
from tests.order_layer.setup_order_layer import setup_order_layer
# @pytest.mark.asyncio
# async def test_invalid_round_start():
#     order_layer, sync_layer, voters, event_system = await setup_order_layer()
#     order_layer._on


@pytest.mark.asyncio
@pytest.mark.parametrize("term_num,round_num", (0, 2), (1, 0))
async def test_pass_messages_with_start_round(term_num, round_num):
    # GIVEN
    order_layer, sync_layer, voters, event_system = await setup_order_layer()

    data = DefaultData(
        id_=b"second",
        prev_id=b'genesis',
        proposer_id=voters[2],
        number=2,
        term_num=term_num,
        round_num=round_num,
        prev_votes=[]
    )
    votes = []
    for i in range(2):
        vote = DefaultVote(
            id_=b"vote_id",
            data_id=b'second',
            commit_id=b'genesis',
            voter_id=voters[0],
            term_num=term_num,
            round_num=round_num
        )
        votes.append(vote)

    order_layer._on_event_received_data(ReceivedDataEvent(data))
    for vote in votes:
        order_layer._on_event_received_vote(ReceivedVoteEvent(vote))

    # WHEN
    term = RotateTerm(term_num, voters)
    order_layer._on_event_start_round(
        StartRoundEvent(
            term=term,
            round_num=round_num
        )
    )

    # THEN
    sync_layer.receive_data.assert_called_once_with(data)

    assert len(sync_layer.receive_vote.call_args_list) == 2
    for i in range(2):
        assert sync_layer.receive_vote.call_args_list[i][0][0] == votes[i]
