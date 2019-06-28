class CommitResult:
    """ from sync layer to async layer
    """
    def __init__(self, result: 'Hash32', data: 'ConsensusData', term: int, _round: int):
        self.result = result
        self.data = data
        self.term = term
        self.round = _round


class CurrentPhaseRequest:
    """ async layer to sync layer
    """
    pass


class CurrentPhaseReply:
    """ sync layer to async layer
    """
    def __init__(self, term: int, _round: int):
        self.term = term
        self.round = _round


class DisposeRound:
    """ sync layer to async layer
    """
    def __init__(self, term: int, _round: int):
        self.term = term
        self.round = _round
