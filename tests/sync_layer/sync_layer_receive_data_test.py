import pytest
from lft.app.vote import DefaultVoteFactory
from lft.consensus.exceptions import InvalidTerm, InvalidRound, AlreadyProposed, AlreadyDataReceived
from tests.sync_layer.setup_items import setup_items


@pytest.mark.asyncio
async def test_sync_layer_invalid_term():
    term_num = 0
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as items:
        voters, event_system, sync_layer, round_layer, genesis_data = items

        data = await sync_layer._data_factory.create_data(0, b'', term_num + 1, 0, [])
        with pytest.raises(InvalidTerm):
            await sync_layer._receive_data(data)


@pytest.mark.asyncio
async def test_sync_layer_invalid_round():
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as items:
        voters, event_system, sync_layer, round_layer, genesis_data = items

        data = await sync_layer._data_factory.create_data(0, b'', 0, round_num + 1, [])
        with pytest.raises(InvalidRound):
            await sync_layer._receive_data(data)


@pytest.mark.asyncio
async def test_sync_layer_already_propose():
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as items:
        voters, event_system, sync_layer, round_layer, genesis_data = items

        data = await sync_layer._data_factory.create_data(
            genesis_data.number + 1, genesis_data.id, genesis_data.term_num, round_num, []
        )
        await sync_layer._receive_data(data)
        with pytest.raises(AlreadyProposed):
            await sync_layer._receive_data(data)


@pytest.mark.asyncio
async def test_sync_layer_data_received():
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as items:
        voters, event_system, sync_layer, round_layer, genesis_data = items

        data = await sync_layer._data_factory.create_data(
            genesis_data.number + 1, genesis_data.id, genesis_data.term_num, round_num, []
        )
        await sync_layer._receive_data(data)
        not_data = await sync_layer._data_factory.create_not_data(
            genesis_data.number, genesis_data.term_num, round_num, genesis_data.proposer_id
        )
        with pytest.raises(AlreadyDataReceived):
            await sync_layer._receive_data(not_data)


@pytest.mark.asyncio
async def test_sync_layer_data_vote_sync():
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as items:
        voters, event_system, sync_layer, round_layer, genesis_data = items

        data = await sync_layer._data_factory.create_data(
            genesis_data.number + 1, genesis_data.id, genesis_data.term_num, round_num, []
        )
        vote_factories = [DefaultVoteFactory(voter) for voter in voters]
        votes = []
        for vote_factory in vote_factories:
            vote = await vote_factory.create_vote(data.id, genesis_data.id, 0, round_num)
            votes.append(vote)
            await sync_layer.receive_vote(vote)

        round_layer.vote_data.assert_not_called()

        await sync_layer.receive_data(data)

        assert len(votes) == len(round_layer.vote_data.call_args_list)
        for vote, call_args in zip(votes, round_layer.vote_data.call_args_list):
            arg_vote, = call_args[0]
            assert arg_vote is vote
