from typing import OrderedDict, DefaultDict, Set, Union
from lft.consensus.messages.data import Data
from lft.consensus.messages.vote import Vote

Datums = OrderedDict[bytes, Data]

Votes = OrderedDict[bytes, Vote]
VotesByDataID = DefaultDict[bytes, OrderedDict[bytes, Vote]]

Voters = Set[bytes]
VotersByDataID = DefaultDict[bytes, Set[bytes]]


class SyncMessages:
    def __init__(self):
        self._datums: Datums = Datums()

        self._votes: Votes = Votes()
        self._votes_by_data_id: VotesByDataID = DefaultDict(OrderedDict)

        self._voters = set()
        self._voters_by_data_id = DefaultDict(set)

    @property
    def datums(self):
        return self._datums.items()

    @property
    def votes(self):
        return self._votes.items()

    @property
    def voters(self):
        return self._voters

    def add_data(self, data: Data):
        self._datums[data.id] = data

    def get_data(self, data_id: bytes, default=None):
        return self._datums.get(data_id, default)

    def add_vote(self, vote: Vote):
        self._votes[vote.id] = vote
        self._votes_by_data_id[vote.data_id][vote.id] = vote

        self._voters.add(vote.voter_id)
        self._voters_by_data_id[vote.data_id].add(vote.voter_id)

    def get_votes(self, data_id: bytes):
        return self._votes_by_data_id[data_id]

    def reach_quorum(self, quorum: int):
        return len(self._voters) >= quorum

    def reach_quorum_consensus(self, quorum: int):
        return any(len(voters) >= quorum for voters in self._voters_by_data_id.values())

    def __contains__(self, item: Union[Data, Vote]):
        if isinstance(item, Data):
            return item.id in self._datums
        if isinstance(item, Vote):
            return item.id in self._votes
        return False
