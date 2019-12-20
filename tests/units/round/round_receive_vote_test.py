import random
import pytest
from lft.app.vote import DefaultVoteFactory
from lft.consensus.round import TIMEOUT_PROPOSE, TIMEOUT_VOTE
from lft.consensus.events import ReceiveDataEvent, ReceiveVoteEvent
from lft.consensus.exceptions import InvalidEpoch, InvalidRound, AlreadyVoted
from lft.event.mediators import DelayedEventMediator
from tests.units.round.setup_items import setup_items


@pytest.mark.asyncio
async def test_round_invalid_epoch():
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as (
            voters, event_system, round_, election, epoch, candidate_data, candidate_votes):

        invalid_epoch_num = epoch.num + 1
        vote = await round_._vote_factory.create_vote(b'test', candidate_data.id, invalid_epoch_num, round_num)
        with pytest.raises(InvalidEpoch):
            await round_._receive_vote(vote)


@pytest.mark.asyncio
async def test_round_invalid_round():
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as (
            voters, event_system, round_, election, epoch, candidate_data, candidate_votes):

        invalid_round_num = round_num + 1
        vote = await round_._vote_factory.create_vote(b'test', candidate_data.id, epoch.num, invalid_round_num)
        with pytest.raises(InvalidRound):
            await round_._receive_vote(vote)


@pytest.mark.asyncio
async def test_round_already_vote():
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as (
            voters, event_system, round_, election, epoch, candidate_data, candidate_votes):

        vote = await round_._vote_factory.create_vote(b'test', candidate_data.id, epoch.num, round_num)
        await round_._receive_vote(vote)

        same_vote = await round_._vote_factory.create_vote(b'test', candidate_data.id, epoch.num, round_num)
        with pytest.raises(AlreadyVoted):
            await round_._receive_vote(same_vote)
        same_vote._id = b'1'
        await round_._receive_vote(same_vote)

        none_vote = round_._vote_factory.create_none_vote(epoch.num, round_num)
        await round_._receive_vote(none_vote)

        same_none_vote = round_._vote_factory.create_none_vote(epoch.num, round_num)
        with pytest.raises(AlreadyVoted):
            await round_._receive_vote(same_none_vote)
        same_none_vote._id = b'3'
        await round_._receive_vote(same_none_vote)


@pytest.mark.asyncio
async def test_round_none_vote_received():
    round_num = 0
    voter_num = 7

    async with setup_items(voter_num, round_num) as (
            voters, event_system, round_, election, epoch, candidate_data, candidate_votes):
        #  Propose NoneData
        await round_.round_start()

        random.shuffle(voters)
        none_votes = []
        for voter in voters[:epoch.quorum_num]:
            none_vote = DefaultVoteFactory(voter).create_none_vote(epoch.num, round_num)
            none_votes.append(none_vote)
            await round_.receive_vote(none_vote)

        assert len(election.receive_vote.call_args_list) == epoch.quorum_num
        for none_vote, call_args in zip(none_votes, election.receive_vote.call_args_list):
            vote, = call_args[0]
            assert vote is none_vote


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num", range(4, 20))
async def test_round_reach_quorum(voter_num: int):
    round_num = 0

    async with setup_items(voter_num, round_num) as (
            voters, event_system, round_, election, epoch, candidate_data, candidate_votes):
        # Propose LazyData
        await round_.round_start()

        mediator = event_system.get_mediator(DelayedEventMediator)
        mediator.execute.assert_called_once()

        delay, event = mediator.execute.call_args_list[0][0]
        assert delay == TIMEOUT_PROPOSE
        assert isinstance(event, ReceiveDataEvent)
        assert event.data.is_lazy()

        mediator.execute.reset_mock()

        random.shuffle(voters)
        vote_factories = [DefaultVoteFactory(voter) for voter in voters]

        quorum_vote_factories = vote_factories[:epoch.quorum_num]
        for vote_factory in quorum_vote_factories[:-1]:
            vote = await vote_factory.create_vote(b"test", candidate_data.id, epoch.num, round_num)
            await round_.receive_vote(vote)

        mediator.execute.assert_not_called()

        none_vote = quorum_vote_factories[-1].create_none_vote(epoch.num, round_num)
        await round_.receive_vote(none_vote)

        assert len(mediator.execute.call_args_list) == len(voters)

        for voter, call_args in zip(voters, mediator.execute.call_args_list):
            timeout, event = call_args[0]
            assert timeout == TIMEOUT_VOTE
            assert isinstance(event, ReceiveVoteEvent)
            assert event.vote.is_lazy()
        mediator.execute.reset_mock()

        none_vote = vote_factories[-1].create_none_vote(epoch.num, round_num)
        await round_.receive_vote(none_vote)

        mediator.execute.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num", range(4, 20))
async def test_round_reach_quorum_consensus(voter_num: int):
    round_num = 0

    async with setup_items(voter_num, round_num) as (
            voters, event_system, round_, election, epoch, candidate_data, candidate_votes):
        # Propose LazyData
        await round_.round_start()

        mediator = event_system.get_mediator(DelayedEventMediator)
        mediator.execute.assert_called_once()

        delay, event = mediator.execute.call_args_list[0][0]
        assert delay == TIMEOUT_PROPOSE
        assert isinstance(event, ReceiveDataEvent)
        assert event.data.is_lazy()

        mediator.execute.reset_mock()

        vote_factories = [DefaultVoteFactory(voter) for voter in voters]
        random.shuffle(vote_factories)

        quorum_vote_factories = vote_factories[:epoch.quorum_num]
        for vote_factory in quorum_vote_factories:
            vote = await vote_factory.create_vote(b'test', candidate_data.id, epoch.num, round_num)
            await round_.receive_vote(vote)

        mediator.execute.assert_not_called()
