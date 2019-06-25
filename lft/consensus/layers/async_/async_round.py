class AsyncRound:
    def __init__(self, term: int, round_: int):
        self.term: int = term
        self.round: int = round_

        self.data = None
        self.vote_events = []
