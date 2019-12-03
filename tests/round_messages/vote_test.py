import os
import random
from lft.app.vote import DefaultVote
from lft.consensus.round import RoundMessages


def test_vote():
    round_messages = RoundMessages()
    assert not round_messages.votes

    vote = _random_vote()
    round_messages.add_vote(vote)

    assert round_messages.votes
    assert vote.id in round_messages.get_votes(vote.data_id)
    assert vote.id not in round_messages.get_votes(os.urandom(16))

    assert vote in round_messages
    assert not (_random_vote() in round_messages)
    assert vote.id not in round_messages
    assert not(vote.id in round_messages)

    for vote_id, vote in round_messages.votes:
        assert vote_id == vote.id
        assert vote is vote


def _random_vote():
    return DefaultVote(id_=os.urandom(16),
                       data_id=os.urandom(16),
                       commit_id=os.urandom(16),
                       voter_id=os.urandom(16),
                       epoch_num=random.randint(0, 100),
                       round_num=random.randint(0, 100))

