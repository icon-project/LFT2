from lft.consensus.data import Data
from lft.consensus.vote import Vote


class CannotComplete(Exception):
    pass


class NotCompleted(Exception):
    pass


class AlreadyCompleted(Exception):
    pass


class AlreadyProposed(Exception):
    def __init__(self, data_id: bytes, proposer_id: bytes):
        self.data_id = data_id
        self.proposer_id = proposer_id


class AlreadyVoted(Exception):
    def __init__(self, vote_id: bytes, voter_id: bytes):
        self.vote_id = vote_id
        self.voter_id = voter_id


class AlreadyDataReceived(Exception):
    pass


class AlreadyVoteReceived(Exception):
    pass


class DataIDNotFound(Exception):
    pass


class InvalidTerm(Exception):
    def __init__(self, term: int, expected: int):
        self.term = term
        self.expected = expected


class InvalidRound(Exception):
    def __init__(self, round_: int, expected: int):
        self.round = round_
        self.expected = expected


class InvalidProposer(Exception):
    def __init__(self, proposer: bytes, expected: bytes):
        self.proposer = proposer
        self.expected = expected


class InvalidVoter(Exception):
    def __init__(self, voter: bytes, expected: bytes):
        self.voter = voter
        self.expected = expected
