from typing import TYPE_CHECKING
from collections import defaultdict

if TYPE_CHECKING:
    from consensus import Consensus
    from consensus.events import ProposeResultEvent, VoteEvent


class DataPool:
    def __init__(self, consensus: 'Consensus'):
        self._consensus = consensus
        self._pool = {}

    def on_event_propose_result(self, event: 'ProposeResultEvent'):
        data = event.data
        self._pool[data.id] = data


class VotePool:
    def __init__(self, consensus: 'Consensus'):
        self._consensus = consensus
        self._pool = defaultdict(dict)

    def on_event_vote(self, event: 'VoteEvent'):
        vote = event.vote
        self._pool[vote.data_id][vote.id] = vote
