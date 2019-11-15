from dataclasses import dataclass
from typing import Sequence, Optional

from lft.consensus.term import Term
from lft.event import Event
from lft.consensus.messages.data import Data, Vote


@dataclass
class InitializeEvent(Event):
    prev_term: Optional['Term']
    term: 'Term'
    round_num: int
    candidate_data: 'Data'
    votes: Sequence['Vote']


@dataclass
class ReceiveDataEvent(Event):
    data: 'Data'


@dataclass
class ReceiveVoteEvent(Event):
    vote: 'Vote'


@dataclass
class BroadcastDataEvent(Event):
    data: 'Data'


@dataclass
class BroadcastVoteEvent(Event):
    vote: 'Vote'


@dataclass
class RoundStartEvent(Event):
    term: Term
    round_num: int


@dataclass
class RoundEndEvent(Event):
    is_success: bool
    term_num: int
    round_num: int
    candidate_data: Optional['Data']
    commit_id: Optional['bytes']
    candidate_votes: Sequence['Vote']


@dataclass
class SyncRequestEvent(Event):
    old_candidate_id: bytes
    new_candidate_id: bytes


@dataclass
class ChangedCandidateEvent(Event):
    candidate_data: Data
    candidate_votes: Sequence[Vote]
