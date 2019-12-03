import os
import pytest

from lft.app.data import DefaultDataFactory
from lft.app.epoch import RotateEpoch
from lft.app.vote import DefaultVoteFactory
from lft.consensus.layers.round import RoundMessages


@pytest.mark.asyncio
async def test_complete_round_success():
    epoch, round_num, round_messages, data, voters = await setup()

    last_vote = await DefaultVoteFactory(voters[-1]).create_vote(data.id, b'', epoch.num, round_num)
    round_messages.add_vote(last_vote)
    round_messages.update()
    candidate = round_messages.result

    assert candidate.proposer_id == voters[0]


@pytest.mark.asyncio
async def test_complete_round_failure_none():
    epoch, round_num, round_messages, data, voters = await setup()

    # Round must add NoneData on RoundStart
    none_data = await DefaultDataFactory(voters[0]).create_none_data(epoch.num, round_num, epoch.get_proposer_id(round_num))
    round_messages.add_data(none_data)

    for voter in voters[:epoch.quorum_num]:
        vote = await DefaultVoteFactory(voter).create_none_vote(epoch.num, round_num)
        round_messages.add_vote(vote)

    round_messages.update()
    candidate = round_messages.result

    assert candidate.is_none()


@pytest.mark.asyncio
async def test_complete_round_failure_lazy():
    epoch, round_num, round_messages, data, voters = await setup()

    # Round must add LazyData on RoundStart
    lazy_data = await DefaultDataFactory(voters[0]).create_lazy_data(epoch.num, round_num, epoch.get_proposer_id(round_num))
    round_messages.add_data(lazy_data)

    for voter in voters[:epoch.quorum_num]:
        vote = await DefaultVoteFactory(voter).create_lazy_vote(voter, epoch.num, round_num)
        round_messages.add_vote(vote)
    round_messages.update()
    candidate = round_messages.result

    assert candidate is None


async def setup():
    epoch_num = 0
    round_num = 0

    voters = [os.urandom(16) for _ in range(7)]
    epoch = RotateEpoch(epoch_num, voters)
    round_messages = RoundMessages(epoch)

    round_messages.update()
    assert round_messages.result is None

    proposer_id = epoch.get_proposer_id(round_num)
    data = await DefaultDataFactory(proposer_id).create_data(0, b'', epoch_num, round_num, [])
    round_messages.add_data(data)

    round_messages.update()
    assert round_messages.result is None

    for voter in voters[:epoch.quorum_num - 1]:
        vote = await DefaultVoteFactory(voter).create_vote(data.id, b'', epoch_num, round_num)
        round_messages.add_vote(vote)

    round_messages.update()
    assert round_messages.result is None

    return epoch, round_num, round_messages, data, voters
