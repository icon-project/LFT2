import os
import pytest

from lft.app.data import DefaultDataFactory
from lft.app.term import RotateTerm
from lft.app.vote import DefaultVoteFactory
from lft.consensus.layers.round import RoundMessages
from lft.consensus.exceptions import DataIDNotFound


@pytest.mark.asyncio
async def test_data_id_not_found():
    term, round_num, round_messages, data, voters = await setup()

    for voter in voters:
        vote = await DefaultVoteFactory(voter).create_vote(data.id, b'', term.num, round_num)
        round_messages.add_vote(vote)

    # This case cannot be handled.
    with pytest.raises(DataIDNotFound):
        round_messages.complete()
    round_messages._is_completed = True

    # This case cannot be handled.
    with pytest.raises(DataIDNotFound):
        round_messages.result()


@pytest.mark.asyncio
async def test_no_data_but_complete_none_vote():
    term, round_num, round_messages, data, voters = await setup()

    for voter in voters:
        vote = await DefaultVoteFactory(voter).create_none_vote(term.num, round_num)
        round_messages.add_vote(vote)

    round_messages.complete()

    candidate = round_messages.result()
    assert candidate.data is None
    assert voters == [vote.voter_id for vote in candidate.votes]


@pytest.mark.asyncio
async def test_no_data_but_complete_not_vote():
    term, round_num, round_messages, data, voters = await setup()

    for voter in voters:
        vote = await DefaultVoteFactory(voter).create_not_vote(voter, term.num, round_num)
        round_messages.add_vote(vote)

    round_messages.complete()

    candidate = round_messages.result()
    assert candidate.data is None
    assert all(voter == vote.voter_id for voter, vote in zip(voters, candidate.votes) if vote is not None)


@pytest.mark.asyncio
async def test_no_data_but_complete_not_none_vote():
    term, round_num, round_messages, data, voters = await setup()

    for voter in voters[:len(voters) // 2]:
        vote = await DefaultVoteFactory(voter).create_not_vote(voter, term.num, round_num)
        round_messages.add_vote(vote)

    for voter in voters[len(voters) // 2:]:
        vote = await DefaultVoteFactory(voter).create_none_vote(term.num, round_num)
        round_messages.add_vote(vote)

    round_messages.complete()

    candidate = round_messages.result()
    assert candidate.data is None
    assert all(voter == vote.voter_id for voter, vote in zip(voters, candidate.votes) if vote is not None)


async def setup():
    term_num = 0
    round_num = 0
    voters = [os.urandom(16) for _ in range(7)]

    term = RotateTerm(term_num, voters)
    round_messages = RoundMessages(term)

    data = await DefaultDataFactory(voters[0]).create_data(0, b'', term.num, round_num, [])
    return term, round_num, round_messages, data, voters

