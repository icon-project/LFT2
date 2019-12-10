import pytest
from lft.app.vote import DefaultVoteFactory
from lft.consensus.exceptions import InvalidEpoch, InvalidRound, AlreadyProposed
from tests.units.round import setup_items


@pytest.mark.asyncio
async def test_round_invalid_epoch():
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as (
            voters, event_system, round_, election, epoch, candidate_data, candidate_votes):

        invalid_epoch_num = epoch.num + 1
        data = await round_._data_factory.create_data(data_number=candidate_data.number + 1,
                                                      prev_id=candidate_data.id,
                                                      epoch_num=invalid_epoch_num,
                                                      round_num=round_num,
                                                      prev_votes=candidate_votes)
        with pytest.raises(InvalidEpoch):
            await round_._receive_data(data)


@pytest.mark.asyncio
async def test_round_invalid_round():
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as (
            voters, event_system, round_, election, epoch, candidate_data, candidate_votes):

        invalid_round_num = round_num + 1
        data = await round_._data_factory.create_data(data_number=candidate_data.number + 1,
                                                      prev_id=candidate_data.id,
                                                      epoch_num=epoch.num,
                                                      round_num=invalid_round_num,
                                                      prev_votes=candidate_votes)
        with pytest.raises(InvalidRound):
            await round_._receive_data(data)


@pytest.mark.asyncio
async def test_round_already_propose():
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as (
            voters, event_system, round_, election, epoch, candidate_data, candidate_votes):

        data = await round_._data_factory.create_data(data_number=candidate_data.number + 1,
                                                      prev_id=candidate_data.id,
                                                      epoch_num=epoch.num,
                                                      round_num=round_num,
                                                      prev_votes=candidate_votes)
        await round_._receive_data(data)
        with pytest.raises(AlreadyProposed):
            await round_._receive_data(data)


@pytest.mark.asyncio
async def test_round_data_vote_sync():
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as (
            voters, event_system, round_, election, epoch, candidate_data, candidate_votes):

        data = await round_._data_factory.create_data(data_number=candidate_data.number + 1,
                                                      prev_id=candidate_data.id,
                                                      epoch_num=epoch.num,
                                                      round_num=round_num,
                                                      prev_votes=candidate_votes)
        vote_factories = [DefaultVoteFactory(voter) for voter in voters]
        votes = []
        for vote_factory in vote_factories:
            vote = await vote_factory.create_vote(data.id, candidate_data.id, epoch.num, round_num)
            votes.append(vote)
            await round_.receive_vote(vote)

        election.receive_vote.assert_not_called()

        await round_.receive_data(data)

        assert len(votes) == len(election.receive_vote.call_args_list)
        for vote, call_args in zip(votes, election.receive_vote.call_args_list):
            arg_vote, = call_args[0]
            assert arg_vote is vote
