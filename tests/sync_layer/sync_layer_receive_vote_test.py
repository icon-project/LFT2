import random
import pytest
from lft.app.vote import DefaultVoteFactory
from lft.consensus.layers.sync.layer import TIMEOUT_PROPOSE, TIMEOUT_VOTE
from lft.consensus.events import ReceiveDataEvent, ReceiveVoteEvent
from lft.consensus.exceptions import InvalidTerm, InvalidRound, AlreadyVoted
from lft.event.mediators import DelayedEventMediator
from tests.sync_layer.setup_items import setup_items


@pytest.mark.asyncio
async def test_sync_layer_invalid_term():
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as (
            voters, event_system, sync_layer, round_layer, term, candidate_data, candidate_votes):

        invalid_term_num = term.num + 1
        vote = await sync_layer._vote_factory.create_vote(b'test', candidate_data.id, invalid_term_num, round_num)
        with pytest.raises(InvalidTerm):
            await sync_layer._receive_vote(vote)


@pytest.mark.asyncio
async def test_sync_layer_invalid_round():
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as (
            voters, event_system, sync_layer, round_layer, term, candidate_data, candidate_votes):

        invalid_round_num = round_num + 1
        vote = await sync_layer._vote_factory.create_vote(b'test', candidate_data.id, term.num, invalid_round_num)
        with pytest.raises(InvalidRound):
            await sync_layer._receive_vote(vote)


@pytest.mark.asyncio
async def test_sync_layer_already_vote():
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as (
            voters, event_system, sync_layer, round_layer, term, candidate_data, candidate_votes):

        vote = await sync_layer._vote_factory.create_vote(b'test', candidate_data.id, term.num, round_num)
        await sync_layer._receive_vote(vote)

        same_vote = await sync_layer._vote_factory.create_vote(b'test', candidate_data.id, term.num, round_num)
        with pytest.raises(AlreadyVoted):
            await sync_layer._receive_vote(same_vote)
        same_vote._id = b'1'
        await sync_layer._receive_vote(same_vote)

        none_vote = await sync_layer._vote_factory.create_none_vote(term.num, round_num)
        await sync_layer._receive_vote(none_vote)

        same_none_vote = await sync_layer._vote_factory.create_none_vote(term.num, round_num)
        with pytest.raises(AlreadyVoted):
            await sync_layer._receive_vote(same_none_vote)
        same_none_vote._id = b'3'
        await sync_layer._receive_vote(same_none_vote)


@pytest.mark.asyncio
async def test_sync_layer_none_vote_received():
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as (
            voters, event_system, sync_layer, round_layer, term, candidate_data, candidate_votes):
        #  Propose NoneData
        await sync_layer.round_start()

        random.shuffle(voters)
        none_votes = []
        for voter in voters[:term.quorum_num]:
            none_vote = await DefaultVoteFactory(voter).create_none_vote(term.num, round_num)
            none_votes.append(none_vote)
            await sync_layer.receive_vote(none_vote)

        assert len(round_layer.vote_data.call_args_list) == term.quorum_num
        for none_vote, call_args in zip(none_votes, round_layer.vote_data.call_args_list):
            vote, = call_args[0]
            assert vote is none_vote


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num", range(4, 20))
async def test_sync_layer_reach_quorum(voter_num: int):
    round_num = 0

    async with setup_items(voter_num, round_num) as (
            voters, event_system, sync_layer, round_layer, term, candidate_data, candidate_votes):
        # Propose NotData
        await sync_layer.round_start()

        mediator = event_system.get_mediator(DelayedEventMediator)
        mediator.execute.assert_called_once()

        delay, event = mediator.execute.call_args_list[0][0]
        assert delay == TIMEOUT_PROPOSE
        assert isinstance(event, ReceiveDataEvent)
        assert event.data.is_not()

        mediator.execute.reset_mock()

        random.shuffle(voters)
        vote_factories = [DefaultVoteFactory(voter) for voter in voters]

        quorum_vote_factories = vote_factories[:term.quorum_num]
        for vote_factory in quorum_vote_factories[:-1]:
            vote = await vote_factory.create_vote(b"test", candidate_data.id, term.num, round_num)
            await sync_layer.receive_vote(vote)

        mediator.execute.assert_not_called()

        none_vote = await quorum_vote_factories[-1].create_none_vote(term.num, round_num)
        await sync_layer.receive_vote(none_vote)

        assert len(mediator.execute.call_args_list) == len(voters)

        for voter, call_args in zip(voters, mediator.execute.call_args_list):
            timeout, event = call_args[0]
            assert timeout == TIMEOUT_VOTE
            assert isinstance(event, ReceiveVoteEvent)
            assert event.vote.is_not()
        mediator.execute.reset_mock()

        none_vote = await vote_factories[-1].create_none_vote(term.num, round_num)
        await sync_layer.receive_vote(none_vote)

        mediator.execute.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num", range(4, 20))
async def test_sync_layer_reach_quorum_consensus(voter_num: int):
    round_num = 0

    async with setup_items(voter_num, round_num) as (
            voters, event_system, sync_layer, round_layer, term, candidate_data, candidate_votes):
        # Propose NotData
        await sync_layer.round_start()

        mediator = event_system.get_mediator(DelayedEventMediator)
        mediator.execute.assert_called_once()

        delay, event = mediator.execute.call_args_list[0][0]
        assert delay == TIMEOUT_PROPOSE
        assert isinstance(event, ReceiveDataEvent)
        assert event.data.is_not()

        mediator.execute.reset_mock()

        vote_factories = [DefaultVoteFactory(voter) for voter in voters]
        random.shuffle(vote_factories)

        quorum_vote_factories = vote_factories[:term.quorum_num]
        for vote_factory in quorum_vote_factories:
            vote = await vote_factory.create_vote(b'test', candidate_data.id, term.num, round_num)
            await sync_layer.receive_vote(vote)

        mediator.execute.assert_not_called()
