import pytest

from lft.app.data import DefaultData
from tests.consensus.setup_consensus import setup_consensus


@pytest.mark.asyncio
async def test_route_message_to_round():
    # GIVEN
    consensus, voters, vote_factories, term, genesis_data = await setup_consensus()

    # WHEN
    for i in range(0, 40, 4):
        data_id = b'id' + bytes([i])
        prev_id = b'id' + bytes([i-1])
        commit_id = b'id' + bytes([i-2])

        prev_votes
        consensus.receive_data(DefaultData(
            id_=data_id,
            prev_id=prev_id,
            proposer_id=voters[0],
            number=i+1,
            term_num=1,
            round_num=i,
            prev_votes=[vote_factory.create_vote(prev_id, commit_id, term_num=1, ) for vote_factory in vote_factories]
        ))
        for vote in [vote_factory.create_vote(data_id) for vote_factory in vote_factories]:
            consensus.receive_vote(vote)

    # THEN

