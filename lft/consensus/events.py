from dataclasses import dataclass
from typing import TYPE_CHECKING, List

from lft.event import Event

if TYPE_CHECKING:
    from lft.consensus.factories import ConsensusData, ConsensusVote


@dataclass
class InitializeEvent(Event):
    """ loopchain to async layer
    """
    candidate_data: ConsensusData
    voters: List[bytes]


@dataclass
class ReceivedConsensusDataEvent(Event):
    """ from loopchain to async layer
    """
    data: ConsensusData


@dataclass
class ReceivedConsensusVoteEvent(Event):
    """ from loopchain to async layer
    """
    vote: ConsensusVote


@dataclass
class BroadcastConsensusDataEvent(Event):
    """ from sync layer to loopchain
    """
    data: ConsensusData
    proposer: bytes


@dataclass
class BroadcastConsensusVoteEvent(Event):
    """ from sync layer to loopchain
    """
    vote: ConsensusVote


@dataclass
class QuorumEvent(Event):
    """ from sync layer to its async layer and loopchain
    """
    candidate_data: ConsensusData
    data: ConsensusData


@dataclass
class ProposeSequence(Event):
    """ from async layer to sync layer
    """
    data: ConsensusData


@dataclass
class VoteSequence(Event):
    """ from async layer to sync layer
    """
    vote: ConsensusVote
