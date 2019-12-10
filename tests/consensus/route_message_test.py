from typing import Tuple, List

import pytest

from lft.app.data import DefaultData
from lft.consensus.messages.data import Data
from lft.consensus.messages.vote import Vote, VoteFactory
from tests.consensus.mocks import RoundMock
from tests.consensus.setup_consensus import setup_consensus


@pytest.mark.asyncio
async def test_route_message_to_round():
    # GIVEN
    consensus, voters, vote_factories, epoch, genesis_data = await setup_consensus()

    # Advance round for test three case
    first_round = RoundMock(epoch, 0)
    # consensus._round_pool.first_round = MagicMock(return_value=first_round)
    await consensus.round_start(epoch, 1)

    # WHEN
    # Three cases one is now round, other one is future round, another is past but acceptable round
    for i in range(3):
        data, votes = await create_sample_items_by_index(i, genesis_data, vote_factories, voters)
        await consensus.receive_data(data)
        for vote in votes:
            await consensus.receive_vote(vote)

    # THEN
    for i in range(3):
        data, votes = await create_sample_items_by_index(i, genesis_data, vote_factories, voters)
        round_ = consensus._round_pool.get_round(epoch.num, i)
        assert consensus._data_pool.get_data(data.id) == data
        for vi, vote in enumerate(votes):
            assert vote == consensus._vote_pool.get_vote(vote.id)
            assert vote == round_.receive_vote.call_args_list[vi][0][0]

        if i != 0:
            prev_round = consensus._round_pool.get_round(epoch.num, i -1)
            for vi, vote in enumerate(data.prev_votes):
                assert vote == consensus._vote_pool.get_vote(vote.id)
                assert vote == prev_round.receive_vote.call_args_list[vi][0][0]


async def create_sample_items_by_index(index: int, genesis_data: Data, vote_factories: List[VoteFactory],
                                       voters: List[bytes]) -> Tuple[Data, List[Vote]]:
    data_id = bytes([index+2])
    prev_id = bytes([index+1])
    commit_id = bytes([index])

    if index == 0:
        prev_votes = []
    else:
        prev_votes = [await vote_factory.create_vote(prev_id, commit_id, 1, index-1)
                      for vote_factory in vote_factories]

    data = DefaultData(
        id_=data_id,
        prev_id=prev_id,
        proposer_id=voters[index],
        number=index+1,
        epoch_num=1,
        round_num=index,
        prev_votes=prev_votes
    )
    votes = [await vote_factory.create_vote(data_id, prev_id, 1, index) for vote_factory in vote_factories]

    return data, votes
