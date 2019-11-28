from typing import Dict, DefaultDict, Set, Optional

from lft.consensus.messages.data import Data, Vote
from lft.consensus.term import Term

Datums = Dict[bytes, Data]  # dict[data_id] = data
Votes = DefaultDict[bytes, Dict[bytes, Vote]]  # dict[data_id][voter_id] = vote


class RoundMessages:
    def __init__(self, term: Term):
        self._term = term

        self._datums: Datums = {}
        self._votes: Votes = DefaultDict(dict)
        self._voters: Set[bytes] = set()
        self._result: Optional[Data] = None

    @property
    def result(self):
        return self._result

    def add_data(self, data: Data):
        self._datums[data.id] = data

    def add_vote(self, vote: Vote):
        self._voters.add(vote.voter_id)
        self._votes[vote.data_id][vote.voter_id] = vote

    def update(self):
        complete_datums = []
        pending_datums = []
        for quorum_data_id in self._find_quorum_data_ids():
            assert quorum_data_id in self._datums

            quorum_data = self._datums[quorum_data_id]
            if quorum_data.is_complete():
                complete_datums.append(quorum_data)
            else:
                pending_datums.append(quorum_data)

        assert len(complete_datums) <= 1
        if complete_datums:
            self._result = complete_datums[0]
            return

        assert len(pending_datums) <= 1
        if pending_datums:
            self._result = pending_datums[0]
            return

        assert len(self._voters) <= self._term.quorum_num
        if len(self._voters) == self._term.quorum_num:
            pending_data = self._find_pending_data()
            assert pending_data
            self._result = pending_data
            return

        self._result = None

    def _find_quorum_data_ids(self):
        return [data_id for data_id, votes_by_data_id in self._votes.items()
                if len(votes_by_data_id) >= self._term.quorum_num]

    def _find_pending_data(self):
        return next((data for data in self._datums.values() if data.is_not()), None)

