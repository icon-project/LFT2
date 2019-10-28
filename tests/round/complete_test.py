import os
import pytest

from lft.app.term import RotateTermFactory
from lft.app.data import DefaultDataFactory
from lft.app.vote import DefaultVoteFactory
from lft.consensus.round import Round
from lft.consensus.exceptions import CannotComplete, AlreadyVoted


@pytest.mark.asyncio
async def test_complete_round_success():
    term, round_, data, voters = await setup()

    last_vote = await DefaultVoteFactory(voters[-1]).create_vote(data.id, b'', term.num, round_.num)
    round_.add_vote(last_vote)
    round_.complete()
    candidate = round_.result()

    assert candidate.data.proposer_id == voters[0]
    assert all(voter == vote.voter_id for voter, vote in zip(voters, candidate.votes) if vote is not None)


@pytest.mark.asyncio
async def test_complete_round_failure_none():
    term, round_, data, voters = await setup()

    for voter in voters[term.quorum_num - 1:]:
        vote = await DefaultVoteFactory(voter).create_none_vote(term.num, round_.num)
        round_.add_vote(vote)
    round_.complete()
    candidate = round_.result()

    assert candidate.data is None
    assert all(voter == vote.voter_id for voter, vote in zip(voters, candidate.votes) if vote is not None)


@pytest.mark.asyncio
async def test_complete_round_failure_not():
    term, round_, data, voters = await setup()

    for voter in voters[term.quorum_num - 1:]:
        vote = await DefaultVoteFactory(voter).create_not_vote(voter, term.num, round_.num)
        round_.add_vote(vote)
    round_.complete()
    candidate = round_.result()

    assert candidate.data is None
    assert all(voter == vote.voter_id for voter, vote in zip(voters, candidate.votes) if vote is not None)


@pytest.mark.asyncio
async def test_complete_round_failure_none_not():
    term, round_, data, voters = await setup()

    for voter in voters[term.quorum_num - 1:-1]:
        vote = await DefaultVoteFactory(voter).create_not_vote(voter, term.num, round_.num)
        round_.add_vote(vote)

    voter = voters[-1]
    vote = await DefaultVoteFactory(voter).create_none_vote(term.num, round_.num)
    round_.add_vote(vote)

    round_.complete()
    candidate = round_.result()

    assert candidate.data is None
    assert all(voter == vote.voter_id for voter, vote in zip(voters, candidate.votes) if vote is not None)


async def setup():
    term_num = 0
    round_num = 0

    voters = [os.urandom(16) for _ in range(7)]
    term = RotateTermFactory(1).create_term(term_num, voters)
    round_ = Round(round_num, term)

    # ValueError(Sequence empty)
    with pytest.raises(CannotComplete):
        round_.complete()

    proposer_id = term.get_proposer_id(round_num)
    data = await DefaultDataFactory(proposer_id).create_data(0, b'', term_num, round_num, [])
    round_.add_data(data)

    # Majority does not reach
    with pytest.raises(CannotComplete):
        round_.complete()

    for voter in voters[:term.quorum_num - 1]:
        vote = await DefaultVoteFactory(voter).create_vote(data.id, b'', term_num, round_num)
        round_.add_vote(vote)

    with pytest.raises(CannotComplete):
        round_.complete()

    return term, round_, data, voters
