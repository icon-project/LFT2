from unittest.mock import patch

import pytest

from lft.app.data import DefaultData
from tests.consensus.setup_consensus import setup_consensus


@pytest.mark.asyncio
async def test_route_message_to_round():
    # GIVEN
    consensus, voters, vote_factories, epoch, genesis_data = await setup_consensus()

    # WHEN
    for i in range(0, 40, 4):
        data_id = b'id' + bytes([i+2])
        prev_id = b'id' + bytes([i+1])
        commit_id = b'id' + bytes([i])

        if i == 0:
            prev_votes = [vote_factory.create_vote(genesis_data.id, genesis_data.id, 0, 0) for vote_factory in vote_factories]
        else:
            prev_votes = [vote_factory.create_vote(prev_id, commit_id, 1, i-1) for vote_factory in vote_factories]
        consensus.receive_data(DefaultData(
            id_=data_id,
            prev_id=prev_id,
            proposer_id=voters[0],
            number=i+1,
            epoch_num=1,
            round_num=i,
            prev_votes=prev_votes
        ))
        for vote in [vote_factory.create_vote(data_id, prev_id, 1, i) for vote_factory in vote_factories]:
            consensus.receive_vote(vote)

    # THEN
    for i in range(0, 40, 4):
        now_round = consensus._new_or_get_round(1, i)
        if i == 0:
            prev_round = consensus._new_or_get_round(0, 0)
            prev_votes = [vote_factory.create_vote(prev_id, genesis_data.id, 0, 0) for vote_factory in vote_factories]
        else:
            prev_round = consensus._new_or_get_round(1, i-1)
            prev_votes = [vote_factory.create_vote(prev_id, commit_id, 1, i-1) for vote_factory in vote_factories]

        votes = [vote_factory.create_vote(data_id, prev_id, 1, i) for vote_factory in vote_factories]
        now_round.receive_data.assert_called_once_with(
            DefaultData(
                id_=data_id,
                prev_id=prev_id,
                proposer_id=voters[0],
                number=i+1,
                epoch_num=1,
                round_num=i,
                prev_votes=prev_votes
            )
        )

        for (index, vote) in enumerate(votes):
            assert now_round.receive_vote.call_args_list[index][0][0] == vote

        for (index, vote) in enumerate(prev_votes):
            assert prev_round.receive_vote.call_args_list[index][0][0] == vote

