import os
import random
from lft.app.vote import DefaultVote
from lft.consensus.layers.sync import SyncMessages


def test_vote():
    sync_messages = SyncMessages()
    assert not sync_messages.datums

    vote = _random_vote()
    sync_messages.add_vote(vote)

    assert sync_messages.votes
    assert vote.id in sync_messages.get_votes(vote.data_id)
    assert vote.id not in sync_messages.get_votes(os.urandom(16))

    assert vote in sync_messages
    assert not (_random_vote() in sync_messages)
    assert vote.id not in sync_messages
    assert not(vote.id in sync_messages)

    for vote_id, vote in sync_messages.votes:
        assert vote_id == vote.id
        assert vote is vote


def _random_vote():
    return DefaultVote(id_=os.urandom(16),
                       data_id=os.urandom(16),
                       commit_id=os.urandom(16),
                       voter_id=os.urandom(16),
                       term_num=random.randint(0, 100),
                       round_num=random.randint(0, 100))
