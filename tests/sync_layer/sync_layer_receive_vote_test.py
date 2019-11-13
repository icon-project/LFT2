import random
import pytest
from lft.app.vote import DefaultVoteFactory
from lft.consensus.layers.sync_layer import TIMEOUT_VOTE
from lft.consensus.events import ReceiveVoteEvent
from lft.consensus.exceptions import InvalidTerm, InvalidRound, AlreadyVoted, AlreadyVoteReceived
from lft.event.mediators import DelayedEventMediator
from tests.sync_layer.setup_items import setup_items


@pytest.mark.asyncio
async def test_sync_layer_invalid_term():
    term_num = 0
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as items:
        voters, event_system, sync_layer, round_layer, genesis_data = items

        vote = await sync_layer._vote_factory.create_vote(b'test', genesis_data.id, term_num + 1, 0)
        with pytest.raises(InvalidTerm):
            await sync_layer._receive_vote(vote)


@pytest.mark.asyncio
async def test_sync_layer_invalid_round():
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as items:
        voters, event_system, sync_layer, round_layer, genesis_data = items

        vote = await sync_layer._vote_factory.create_vote(b'test', genesis_data.id, 0, round_num + 1)
        with pytest.raises(InvalidRound):
            await sync_layer._receive_vote(vote)


@pytest.mark.asyncio
async def test_sync_layer_already_vote():
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as items:
        voters, event_system, sync_layer, round_layer, genesis_data = items

        vote = await sync_layer._vote_factory.create_vote(b'test', genesis_data.id, 0, round_num)
        await sync_layer._receive_vote(vote)

        same_vote = await sync_layer._vote_factory.create_vote(b'test', genesis_data.id, 0, round_num)
        with pytest.raises(AlreadyVoted):
            await sync_layer._receive_vote(same_vote)
        same_vote._id = b'1'
        await sync_layer._receive_vote(same_vote)

        none_vote = await sync_layer._vote_factory.create_none_vote(0, round_num)
        await sync_layer._receive_vote(none_vote)

        same_none_vote = await sync_layer._vote_factory.create_none_vote(0, round_num)
        with pytest.raises(AlreadyVoted):
            await sync_layer._receive_vote(same_none_vote)
        same_none_vote._id = b'3'
        await sync_layer._receive_vote(same_none_vote)


@pytest.mark.asyncio
async def test_sync_layer_already_vote_received():
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as items:
        voters, event_system, sync_layer, round_layer, genesis_data = items

        vote = await sync_layer._vote_factory.create_vote(b'test', b'', 0, round_num)
        await sync_layer._receive_vote(vote)

        not_vote = await sync_layer._vote_factory.create_not_vote(voters[0], 0, round_num)
        with pytest.raises(AlreadyVoteReceived):
            await sync_layer._receive_vote(not_vote)


@pytest.mark.asyncio
async def test_sync_layer_none_vote_received():
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as items:
        voters, event_system, sync_layer, round_layer, genesis_data = items

        random.shuffle(voters)
        none_votes = []
        for voter in voters[:sync_layer._term.quorum_num]:
            none_vote = await DefaultVoteFactory(voter).create_none_vote(0, round_num)
            none_votes.append(none_vote)
            await sync_layer.receive_vote(none_vote)

        assert len(round_layer.vote_data.call_args_list) == sync_layer._term.quorum_num
        for none_vote, call_args in zip(none_votes, round_layer.vote_data.call_args_list):
            vote, = call_args[0]
            assert vote is none_vote


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num", range(4, 20))
async def test_sync_layer_reach_quorum(voter_num: int):
    round_num = 0

    async with setup_items(voter_num, round_num) as items:
        voters, event_system, sync_layer, round_layer, genesis_data = items

        vote_factories = [DefaultVoteFactory(voter) for voter in voters]
        random.shuffle(vote_factories)

        quorum_vote_factories = vote_factories[:sync_layer._term.quorum_num]
        for vote_factory in quorum_vote_factories[:-1]:
            vote = await vote_factory.create_vote(genesis_data.id, genesis_data.prev_id, 0, round_num)
            await sync_layer._receive_vote(vote)

        mediator = event_system.get_mediator(DelayedEventMediator)
        mediator.execute.assert_not_called()

        none_vote = await vote_factories[-1].create_none_vote(0, round_num)
        await sync_layer._receive_vote(none_vote)

        assert len(voters) == len(mediator.execute.call_args_list)
        for voter, call_args in zip(voters, mediator.execute.call_args_list):
            timeout, event = call_args[0]
            assert timeout == TIMEOUT_VOTE
            assert isinstance(event, ReceiveVoteEvent)
            assert event.vote.is_not()
            assert event.vote.voter_id == voter

        none_vote = await vote_factories[-2].create_none_vote(0, round_num)
        await sync_layer._receive_vote(none_vote)

        assert len(voters) == len(mediator.execute.call_args_list)


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num", range(4, 20))
async def test_sync_layer_reach_quorum_consensus(voter_num: int):
    round_num = 0

    async with setup_items(voter_num, round_num) as items:
        voters, event_system, sync_layer, round_layer, genesis_data = items

        vote_factories = [DefaultVoteFactory(voter) for voter in voters]
        random.shuffle(vote_factories)

        quorum_vote_factories = vote_factories[:sync_layer._term.quorum_num]
        for vote_factory in quorum_vote_factories:
            vote = await vote_factory.create_vote(genesis_data.id, genesis_data.prev_id, 0, round_num)
            await sync_layer._receive_vote(vote)

        mediator = event_system.get_mediator(DelayedEventMediator)
        mediator.execute.assert_not_called()
