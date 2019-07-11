class AsyncRound:
    def __init__(self, term_num: int, round_num: int):
        self.term_num: int = term_num
        self.round_num: int = round_num

        self.data = None
        self.vote_events = []
