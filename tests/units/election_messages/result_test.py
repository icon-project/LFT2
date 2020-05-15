import os
import pytest

from lft.app.data import DefaultDataFactory
from lft.app.vote import DefaultVoteFactory, DefaultVote
from lft.app.epoch import RotateEpoch
from lft.consensus.election import ElectionMessages


@pytest.mark.asyncio
async def test_round_success():
    epoch, round_num, election_messages, data, voters = await setup()

    last_vote = await DefaultVoteFactory(voters[-1]).create_vote(data.id, b'', epoch.num, round_num)
    election_messages.add_vote(last_vote)
    election_messages.update()
    candidate = election_messages.result

    assert candidate.proposer_id == voters[0]


@pytest.mark.asyncio
async def test_round_failure_none():
    epoch, round_num, election_messages, data, voters = await setup()

    # Round must add NoneData on RoundStart
    none_data = DefaultDataFactory(voters[0]).create_none_data(epoch.num, round_num, epoch.get_proposer_id(round_num))
    election_messages.add_data(none_data)

    for voter in voters[:epoch.quorum_num]:
        vote = DefaultVoteFactory(voter).create_none_vote(epoch.num, round_num)
        election_messages.add_vote(vote)

    election_messages.update()
    candidate = election_messages.result

    assert candidate.is_none()


@pytest.mark.asyncio
async def test_round_failure_lazy():
    epoch, round_num, election_messages, data, voters = await setup()

    # Round must add LazyData on RoundStart
    lazy_data = DefaultDataFactory(voters[0]).create_lazy_data(epoch.num, round_num, epoch.get_proposer_id(round_num))
    election_messages.add_data(lazy_data)

    for voter in voters[:epoch.quorum_num]:
        vote = DefaultVoteFactory(voter).create_lazy_vote(voter, epoch.num, round_num)
        election_messages.add_vote(vote)
    election_messages.update()
    candidate = election_messages.result

    assert candidate is None


@pytest.mark.asyncio
async def test_round_failure_consensus_id():
    class FakeVote(DefaultVote):
        @property
        def consensus_id(self) -> bytes:
            return b'abcd'

    epoch, round_num, election_messages, data, voters = await setup()

    last_vote = await DefaultVoteFactory(voters[-1]).create_vote(data.id, b'', epoch.num, round_num)
    last_vote.__class__ = FakeVote
    election_messages.add_vote(last_vote)
    election_messages.update()
    candidate = election_messages.result

    assert candidate is None


async def setup():
    epoch_num = 0
    round_num = 0

    voters = [os.urandom(16) for _ in range(7)]
    epoch = RotateEpoch(epoch_num, voters)
    election_messages = ElectionMessages(epoch, round_num, DefaultDataFactory(voters[0]))

    election_messages.update()
    assert election_messages.result is None

    proposer_id = epoch.get_proposer_id(round_num)
    data = await DefaultDataFactory(proposer_id).create_data(0, b'', epoch_num, round_num, [])
    election_messages.add_data(data)

    election_messages.update()
    assert election_messages.result is None

    for voter in voters[:epoch.quorum_num - 1]:
        vote = await DefaultVoteFactory(voter).create_vote(data.id, b'', epoch_num, round_num)
        election_messages.add_vote(vote)

    election_messages.update()
    assert election_messages.result is None

    return epoch, round_num, election_messages, data, voters
