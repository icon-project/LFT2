class AlreadyProposed(Exception):
    def __init__(self, data_id: bytes, proposer_id: bytes):
        self.data_id = data_id
        self.proposer_id = proposer_id


class AlreadyVoted(Exception):
    def __init__(self, vote_id: bytes, voter_id: bytes):
        self.vote_id = vote_id
        self.voter_id = voter_id


class AlreadyCandidate(Exception):
    pass


class AlreadySync(Exception):
    def __init__(self, data_id: bytes):
        self.data_id = data_id


class InvalidEpoch(Exception):
    def __init__(self, epoch: int, expected: int):
        self.epoch = epoch
        self.expected = expected


class InvalidRound(Exception):
    def __init__(self, epoch: int, round_: int, expected_epoch: int, expected_round: int):
        self.epoch = epoch
        self.round = round_
        self.expected_epoch = expected_epoch
        self.expected_round = expected_round


class InvalidProposer(Exception):
    def __init__(self, proposer: bytes, expected: bytes):
        self.proposer = proposer
        self.expected = expected


class InvalidVoter(Exception):
    def __init__(self, voter: bytes, expected: bytes):
        self.voter = voter
        self.expected = expected


class ReachCandidate(Exception):
    def __init__(self, candidate_data, candidate_votes):
        self.candidate_data = candidate_data
        self.candidate_votes = candidate_votes


class NeedSync(Exception):
    def __init__(self, old_candidate_id: bytes, new_candidate_id: bytes):
        self.new_candidate_id = new_candidate_id
        self.old_candidate_id = old_candidate_id


class NotReachCandidate(Exception):
    pass

