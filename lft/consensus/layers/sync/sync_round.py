class SyncRound:
    def __init__(self, term: int, round_: int, data, votes):
        self.term: int = term
        self.round: int = round_

        self.data = data
        self.votes = votes
        self.expired = False

