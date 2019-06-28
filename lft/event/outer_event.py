from lft.consensus.factories import ConsensusData, ConsensusVote


# 초기화 후, 받는 data에 맞는 round를 생성하고 그것과 저장되어 있는 마지막 정보의 차이를 근거로 다음 동작을 해야 하나 ?
# sync를 요청하거나 계속 해당 round data 수집 후 합의를 진행 ..
class InitializeLastData:
    """ loopchain to async layer
    """
    def __init__(self, term: int, _round: int):
        self.term = term
        self.round = _round


class ProposeData:
    """ from loopchain to async layer
    """
    def __init__(self, data: 'ConsensusData', term: int, _round: int, proposer: 'Hash32'):
        self.data = data
        self.term = term
        self.round = _round
        self.proposer = proposer


class BroadcastProposeData:
    """ from sync layer to loopchain ? async layer ?
    """
    def __init__(self, data: 'ConsensusData', term: int, _round: int, proposer: 'Hash32'):
        self.data = data
        self.term = term
        self.round = _round
        self.proposer = proposer


class Vote:
    """ from loopchain to async layer
    """
    def __init__(self, vote: 'ConsensusVote'):
        self.vote = vote


class BroadcastVote:
    """ from sync layer? async layer? to loopchain
    """
    def __init__(self, vote: 'ConsensusVote'):
        self.vote = vote


# data엔 어떤 값들이 있는걸까 ?
class CompleteCommit:
    """ from sync layer to loopchain
    """
    def __init__(self, result: 'Hash32', data: 'ConsensusData', term: int, _round: int):
        self.result = result
        self.data = data
        self.term = term
        self.round = _round


# sync는 하나씩 할지, 아님 여러개를 동시에 할지 ?
class SyncRequest:
    """ from async layer to loopchain
    """
    def __init__(self, height: int, term: int = None, _round: int = None):
        self.height = height
        self.term = term
        self.round = _round


# data에 어떤 값들이 있느냐에 따라 height 필요여부 결정
class SyncResult:
    """ from loopchain to async
    """
    def __init__(self, data: 'ConsensusData', height: int, term: int, _round: int):
        self.data = data
        self.height = height
        self.term = term
        self.round = _round

