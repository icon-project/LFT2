from typing import Dict, DefaultDict, OrderedDict, Set, Optional

from lft.consensus.messages.data import Data, Vote
from lft.consensus.epoch import Epoch

Datums = OrderedDict[bytes, Data]  # dict[data_id] = data
Votes = DefaultDict[bytes, Dict[bytes, Vote]]  # dict[data_id][voter_id] = vote


class RoundMessages:
    def __init__(self, epoch: Epoch):
        self._epoch = epoch

        self._datums: Datums = OrderedDict()
        self._votes: Votes = DefaultDict(dict)
        self._voters: Set[bytes] = set()
        self._result: Optional[Data] = None

    @property
    def result(self):
        return self._result

    @property
    def first_real_data(self):
        return next((data for data in self._datums.values() if data.is_real()), None)

    def add_data(self, data: Data):
        self._datums[data.id] = data

    def add_vote(self, vote: Vote):
        self._voters.add(vote.voter_id)
        self._votes[vote.data_id][vote.voter_id] = vote

    def update(self):
        # RealData : Deepochine round success and round end
        # NoneData : Deepochine round failure and round end
        # LazyData : Cannot deepochine but round end
        # None : Nothing changes

        if self._update_quorum_data():
            return

        if self._update_possible_data():
            return

        if self._update_lazy_data():
            return

        self._result = None

    def _update_quorum_data(self):
        quorum_datums = [data for data in self._datums.values()
                         if len(self._votes[data.id]) >= self._epoch.quorum_num]
        quorum_datums.sort(key=lambda data: not data.is_complete())
        assert ((len(quorum_datums) <= 1) or
                (len(quorum_datums) == 2 and quorum_datums[0].is_complete() and quorum_datums[1].is_lazy()))

        if quorum_datums and quorum_datums[0].is_complete():
            self._result = quorum_datums[0]
            return True
        return False

    def _update_possible_data(self):
        unvoter = self._get_unvoters()
        if len(unvoter) >= self._epoch.quorum_num:
            return False

        possible_datums = [data for data in self._datums.values()
                           if data.is_real()
                           if len(self._votes[data.id]) < self._epoch.quorum_num
                           if len(self._votes[data.id]) + len(unvoter) >= self._epoch.quorum_num]

        if not possible_datums:
            self._result = self._find_none_data()
            return True

        return False

    def _update_lazy_data(self):
        assert len(self._voters) <= len(self._epoch.voters)
        if len(self._voters) == len(self._epoch.voters):
            self._result = self._find_lazy_data()
            return True
        return False

    def _find_none_data(self):
        try:
            return next(data for data in self._datums.values() if data.is_none())
        except StopIteration:
            assert "NoneData does not exist"

    def _find_lazy_data(self):
        try:
            return next(data for data in self._datums.values() if data.is_lazy())
        except StopIteration:
            assert "LazyData does not exist"

    def _get_unvoters(self):
        return set(self._epoch.voters) - self._voters


