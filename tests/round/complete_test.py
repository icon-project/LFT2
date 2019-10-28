import os
import pytest

from lft.app.term import RotateTermFactory
from lft.app.data import DefaultDataFactory
from lft.app.vote import DefaultVoteFactory
from lft.consensus.round import Round
from lft.consensus.exceptions import CannotComplete


@pytest.mark.asyncio
async def test_complete():
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

    #
    with pytest.raises(CannotComplete):
        round_.complete()

    quorum = len(voters) * 2 // 3 + 1
    for voter in voters[:quorum]:
        vote = await DefaultVoteFactory(voter).create_vote(data.id, b'', term_num, round_num)
        round_.add_vote(vote)

    with pytest.raises(CannotComplete):
        round_.add_vote()
