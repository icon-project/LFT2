
class CannotComplete(Exception):
    pass


class AlreadyCompleted(Exception):
    pass


class NotCompleted(Exception):
    pass


class AlreadyProposed(Exception):
    pass


class AlreadyVoted(Exception):
    pass


class DataIDNotFound(Exception):
    pass


class InvalidProposer(Exception):
    def __init__(self, proposer: bytes, expected: bytes):
        self.proposer = proposer
        self.expected = expected


class InvalidVoter(Exception):
    def __init__(self, voter: bytes, expected: bytes):
        self.voter = voter
        self.expected = expected
