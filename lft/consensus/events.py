from dataclasses import dataclass
from typing import Sequence, Optional

from lft.event import Event
from lft.consensus.data import ConsensusData, ConsensusVote

@dataclass
class InitializeEvent(Event):
    """ application to async layer
    """
    term_num: int
    round_num: int
    node_id: bytes
    candidate_data: 'ConsensusData'
    voters: Sequence[bytes]


@dataclass
class ReceivedConsensusDataEvent(Event):
    """ from application to async layer
    """
    data: 'ConsensusData'


@dataclass
class ReceivedConsensusVoteEvent(Event):
    """ from application to async layer
    """
    vote: 'ConsensusVote'


@dataclass
class BroadcastConsensusDataEvent(Event):
    """ from sync layer to application
    """
    data: 'ConsensusData'


@dataclass
class BroadcastConsensusVoteEvent(Event):
    """ from sync layer to application
    """
    vote: 'ConsensusVote'


@dataclass
class DoneRoundEvent(Event):
    """ from sync layer to its async layer and application
    """
    is_success: bool
    term_num: int
    round_num: int
    candidate_data: Optional['ConsensusData']
    commit_data: Optional['ConsensusData']
    votes: Sequence['ConsensusVote']


@dataclass
class ProposeSequence(Event):
    """ from async layer to sync layer
    """
    data: 'ConsensusData'


@dataclass
class VoteSequence(Event):
    """ from async layer to sync layer
    """
    vote: 'ConsensusVote'
