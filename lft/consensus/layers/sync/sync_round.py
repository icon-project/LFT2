class SyncRound:
    def __init__(self, term_num: int, round_num: int, data, votes):
        self.term_num: int = term_num
        self.round_num: int = round_num

        self.data = data
        self.votes = votes
        self.expired = False

