import pytest
from lft.app.vote import DefaultVoteFactory
from lft.consensus.exceptions import InvalidTerm, InvalidRound, AlreadyProposed
from tests.sync_layer.setup_items import setup_items


@pytest.mark.asyncio
async def test_sync_layer_invalid_term():
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as (
            voters, event_system, sync_layer, round_layer, term, candidate_data, candidate_votes):

        invalid_term_num = term.num + 1
        data = await sync_layer._data_factory.create_data(data_number=candidate_data.number + 1,
                                                          prev_id=candidate_data.id,
                                                          term_num=invalid_term_num,
                                                          round_num=round_num,
                                                          prev_votes=candidate_votes)
        with pytest.raises(InvalidTerm):
            await sync_layer._receive_data(data)


@pytest.mark.asyncio
async def test_sync_layer_invalid_round():
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as (
            voters, event_system, sync_layer, round_layer, term, candidate_data, candidate_votes):

        invalid_round_num = round_num + 1
        data = await sync_layer._data_factory.create_data(data_number=candidate_data.number + 1,
                                                          prev_id=candidate_data.id,
                                                          term_num=term.num,
                                                          round_num=invalid_round_num,
                                                          prev_votes=candidate_votes)
        with pytest.raises(InvalidRound):
            await sync_layer._receive_data(data)


@pytest.mark.asyncio
async def test_sync_layer_already_propose():
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as (
            voters, event_system, sync_layer, round_layer, term, candidate_data, candidate_votes):

        data = await sync_layer._data_factory.create_data(data_number=candidate_data.number + 1,
                                                          prev_id=candidate_data.id,
                                                          term_num=term.num,
                                                          round_num=round_num,
                                                          prev_votes=candidate_votes)
        await sync_layer._receive_data(data)
        with pytest.raises(AlreadyProposed):
            await sync_layer._receive_data(data)


@pytest.mark.asyncio
async def test_sync_layer_data_vote_sync():
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as (
            voters, event_system, sync_layer, round_layer, term, candidate_data, candidate_votes):

        data = await sync_layer._data_factory.create_data(data_number=candidate_data.number + 1,
                                                          prev_id=candidate_data.id,
                                                          term_num=term.num,
                                                          round_num=round_num,
                                                          prev_votes=candidate_votes)
        vote_factories = [DefaultVoteFactory(voter) for voter in voters]
        votes = []
        for vote_factory in vote_factories:
            vote = await vote_factory.create_vote(data.id, candidate_data.id, term.num, round_num)
            votes.append(vote)
            await sync_layer.receive_vote(vote)

        round_layer.vote_data.assert_not_called()

        await sync_layer.receive_data(data)

        assert len(votes) == len(round_layer.vote_data.call_args_list)
        for vote, call_args in zip(votes, round_layer.vote_data.call_args_list):
            arg_vote, = call_args[0]
            assert arg_vote is vote