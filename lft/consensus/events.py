from dataclasses import dataclass
from typing import Sequence
from lft.event import Event
from lft.consensus.data import ConsensusData, ConsensusVote

@dataclass
class InitializeEvent(Event):
    """ application to async layer
    """
    term_num: int
    round_num: int
    candidate_data: 'ConsensusData'
    voters: Sequence[bytes]


@dataclass
class ReceivedConsensusDataEvent(Event):
    """ from application to async layer
    """
    deterministic = False

    data: 'ConsensusData'


@dataclass
class ReceivedConsensusVoteEvent(Event):
    """ from application to async layer
    """
    deterministic = False

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
    term_num: int
    round_num: int
    candidate_data: 'ConsensusData'
    commit_data: 'ConsensusData'


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


@dataclass
class DoneRoundEvent(Event):
    """ When the round is done sync layer raises this event
    """
    term_num: int
    round_num: int
    round_result: bool

