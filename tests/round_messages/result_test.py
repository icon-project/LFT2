import os
import pytest

from lft.app.data import DefaultDataFactory
from lft.app.term import RotateTerm
from lft.app.vote import DefaultVoteFactory
from lft.consensus.layers.round import RoundMessages


@pytest.mark.asyncio
async def test_complete_round_success():
    term, round_num, round_messages, data, voters = await setup()

    last_vote = await DefaultVoteFactory(voters[-1]).create_vote(data.id, b'', term.num, round_num)
    round_messages.add_vote(last_vote)
    round_messages.update()
    candidate = round_messages.result

    assert candidate.proposer_id == voters[0]


@pytest.mark.asyncio
async def test_complete_round_failure_none():
    term, round_num, round_messages, data, voters = await setup()

    # Round must add NoneData on RoundStart
    none_data = await DefaultDataFactory(voters[0]).create_none_data(term.num, round_num, term.get_proposer_id(round_num))
    round_messages.add_data(none_data)

    for voter in voters[:term.quorum_num]:
        vote = await DefaultVoteFactory(voter).create_none_vote(term.num, round_num)
        round_messages.add_vote(vote)

    round_messages.update()
    candidate = round_messages.result

    assert candidate.is_none()


@pytest.mark.asyncio
async def test_complete_round_failure_lazy():
    term, round_num, round_messages, data, voters = await setup()

    # Round must add LazyData on RoundStart
    lazy_data = await DefaultDataFactory(voters[0]).create_lazy_data(term.num, round_num, term.get_proposer_id(round_num))
    round_messages.add_data(lazy_data)

    for voter in voters[:term.quorum_num]:
        vote = await DefaultVoteFactory(voter).create_lazy_vote(voter, term.num, round_num)
        round_messages.add_vote(vote)
    round_messages.update()
    candidate = round_messages.result

    assert candidate is None


async def setup():
    term_num = 0
    round_num = 0

    voters = [os.urandom(16) for _ in range(7)]
    term = RotateTerm(term_num, voters)
    round_messages = RoundMessages(term)

    round_messages.update()
    assert round_messages.result is None

    proposer_id = term.get_proposer_id(round_num)
    data = await DefaultDataFactory(proposer_id).create_data(0, b'', term_num, round_num, [])
    round_messages.add_data(data)

    round_messages.update()
    assert round_messages.result is None

    for voter in voters[:term.quorum_num - 1]:
        vote = await DefaultVoteFactory(voter).create_vote(data.id, b'', term_num, round_num)
        round_messages.add_vote(vote)

    round_messages.update()
    assert round_messages.result is None

    return term, round_num, round_messages, data, voters
