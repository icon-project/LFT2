from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from consensus.factories import ConsensusData, ConsensusVote, ConsensusVotes


class RoundEvent:
    def __init__(self, round_: int, leader_id):
        self.round = round_
        self.leader_id = leader_id


class ProposeResultEvent:
    def __init__(self, data: 'ConsensusData'):
        self.data = data


class VoteEvent:
    def __init__(self, vote: 'ConsensusVote'):
        self.vote = vote


class VoteResultEvent:
    def __init__(self, votes: 'ConsensusVotes'):
        self.votes = votes


class CommitResultEvent:
    def __init__(self, data: 'ConsensusData'):
        self.data = data
