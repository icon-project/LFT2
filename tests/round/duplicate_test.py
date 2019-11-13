import os
import pytest

from lft.app.data import DefaultDataFactory
from lft.app.term import RotateTerm
from lft.app.vote import DefaultVoteFactory
from lft.consensus.layers.round import RoundMessages
from lft.consensus.exceptions import AlreadyVoted


@pytest.mark.asyncio
async def test_vote_duplicate():
    term_num = 0
    round_num = 0
    voters = [os.urandom(16) for _ in range(7)]

    term = RotateTerm(term_num, voters)
    round_messages = RoundMessages(term)

    data = await DefaultDataFactory(voters[0]).create_data(0, b'', term_num, round_num, [])
    vote = await DefaultVoteFactory(voters[0]).create_vote(data.id, b'', term_num, term_num)

    round_messages.add_vote(vote)

    duplicate_vote = await DefaultVoteFactory(voters[0]).create_vote(data.id, b'', term_num, term_num)
    with pytest.raises(AlreadyVoted):
        round_messages.add_vote(duplicate_vote)

