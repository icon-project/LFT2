from dataclasses import dataclass
from typing import Sequence, Optional

from lft.consensus.term import Term
from lft.event import Event
from lft.consensus.data import Data, Vote


@dataclass
class InitializeEvent(Event):
    """ application to async layer
    """
    term: 'Term'
    round_num: int
    candidate_data: 'Data'
    votes: Sequence['Vote']


@dataclass
class ReceivedDataEvent(Event):
    """ from application to async layer
    """
    data: 'Data'


@dataclass
class ReceivedVoteEvent(Event):
    """ from application to async layer
    """
    vote: 'Vote'


@dataclass
class BroadcastDataEvent(Event):
    """ from sync layer to application
    """
    data: 'Data'


@dataclass
class BroadcastVoteEvent(Event):
    """ from sync layer to application
    """
    vote: 'Vote'


@dataclass
class DoneRoundEvent(Event):
    """ from sync layer to its async layer and application
    """
    is_success: bool
    term_num: int
    round_num: int
    candidate_data: Optional['Data']
    commit_id: Optional['bytes']
    votes: Sequence['Vote']


@dataclass
class StartRoundEvent(Event):
    term: Term
    round_num: int


@dataclass(eq=True)
class SyncRequestEvent(Event):
    old_candidate_id: bytes
    new_candidate_id: bytes


@dataclass
class ChangedCandidateEvent(Event):
    candidate_data: Data
    candidate_votes: Sequence[Vote]
