from typing import Dict, DefaultDict, OrderedDict, Set, Optional

from lft.consensus.messages.data import Data, Vote
from lft.consensus.term import Term

Datums = OrderedDict[bytes, Data]  # dict[data_id] = data
Votes = DefaultDict[bytes, Dict[bytes, Vote]]  # dict[data_id][voter_id] = vote


class RoundMessages:
    def __init__(self, term: Term):
        self._term = term

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
        # RealData : Determine round success and round end
        # NoneData : Determine round failure and round end
        # NotData : Cannot determine but round end
        # None : Nothing changes

        quorum_datums = []
        possible_datums = []

        unvoters = self._get_unvoters()
        for data in self._datums.values():
            votes = self._votes[data.id]
            if len(votes) >= self._term.quorum_num:
                quorum_datums.append(data)
            else:
                if len(votes) + len(unvoters) >= self._term.quorum_num:
                    possible_datums.append(data)

        assert len(quorum_datums) <= 2  # complete data + not data
        if quorum_datums:
            if len(quorum_datums) == 1:
                self._result = quorum_datums[0]
            else:
                self._result = quorum_datums[0] if quorum_datums[0].is_complete() else quorum_datums[1]
            return

        if not possible_datums:
            self._result = self._find_none_data()
            return

        assert len(self._voters) <= len(self._term.voters)
        if len(self._voters) == len(self._term.voters):
            self._result = self._find_not_data()
            return

        self._result = None

    def _find_not_data(self):
        try:
            return next(data for data in self._datums.values() if data.is_not())
        except StopIteration:
            assert "NotData does not exist"

    def _find_none_data(self):
        try:
            return next(data for data in self._datums.values() if data.is_none())
        except StopIteration:
            assert "NoneData does not exist"

    def _get_unvoters(self):
        return set(self._term.voters) - self._voters


