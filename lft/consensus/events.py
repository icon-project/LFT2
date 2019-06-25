from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from lft.consensus.factories import ConsensusData, ConsensusVote, ConsensusVotes


class ProposeEvent:
    def __init__(self, data: 'ConsensusData', era: int, round_: int, leader: bytes):
        self.data = data
        self.era = era
        self.round = round_
        self.leader = leader


class VoteEvent:
    def __init__(self, vote: 'ConsensusVote'):
        self.vote = vote


class VoteResultEvent:
    def __init__(self, votes: 'ConsensusVotes'):
        self.votes = votes


class CommitResultEvent:
    def __init__(self, data: 'ConsensusData'):
        self.data = data


ProposeSequence = ProposeEvent
VoteSequence = VoteEvent
