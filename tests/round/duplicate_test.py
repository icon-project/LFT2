import os
import pytest

from lft.app.term import RotateTermFactory
from lft.app.data import DefaultDataFactory
from lft.app.vote import DefaultVoteFactory
from lft.consensus.round import Round
from lft.consensus.exceptions import AlreadyVoted


@pytest.mark.asyncio
async def test_vote_duplicate():
    term_num = 0
    round_num = 0
    voters = [os.urandom(16) for _ in range(7)]

    term = RotateTermFactory(1).create_term(term_num, voters)
    round_ = Round(round_num, term)

    data = await DefaultDataFactory(voters[0]).create_data(0, b'', term_num, round_num, [])
    vote = await DefaultVoteFactory(voters[0]).create_vote(data.id, b'', term_num, term_num)

    round_.add_vote(vote)

    duplicate_vote = await DefaultVoteFactory(voters[0]).create_vote(data.id, b'', term_num, term_num)
    with pytest.raises(AlreadyVoted):
        round_.add_vote(duplicate_vote)

