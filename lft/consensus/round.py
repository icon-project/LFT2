import logging
from bisect import insort
from typing import List, OrderedDict, DefaultDict, Set, Union, Sequence
from lft.consensus.messages.data import Data, DataFactory
from lft.consensus.messages.vote import Vote, VoteFactory
from lft.consensus.events import ReceiveDataEvent, ReceiveVoteEvent
from lft.consensus.epoch import Epoch
from lft.consensus.election import Election
from lft.consensus.exceptions import InvalidRound, InvalidEpoch, AlreadyProposed, AlreadyVoted
from lft.event import EventSystem
from lft.event.mediators import DelayedEventMediator


__all__ = ("Round", "RoundMessages", "RoundPool", "TIMEOUT_PROPOSE", "TIMEOUT_VOTE")

TIMEOUT_PROPOSE = 2.0
TIMEOUT_VOTE = 2.0


class Round:
    def __init__(self,
                 election: Election,
                 node_id: bytes,
                 epoch: Epoch,
                 round_num: int,
                 event_system: EventSystem,
                 data_factory: DataFactory,
                 vote_factory: VoteFactory):
        self._election = election
        self._node_id = node_id

        self._epoch = epoch
        self._num = round_num

        self._event_system = event_system
        self._data_factory = data_factory
        self._vote_factory = vote_factory

        self._logger = logging.getLogger(node_id.hex())
        self._messages = RoundMessages()

        self._vote_timeout_started = False

    @property
    def num(self):
        return self._num

    @property
    def epoch_num(self):
        return self._epoch.num

    @property
    def result_id(self):
        return self._election.result_id

    @property
    def candidate_id(self):
        return self._election._candidate_id

    @candidate_id.setter
    def candidate_id(self, new_candidate_id: bytes):
        self._election._candidate_id = new_candidate_id

    async def round_start(self):
        await self._new_unreal_datums()
        await self._election.round_start()

    async def receive_data(self, data: Data):
        try:
            await self._receive_data(data)
        except (InvalidEpoch, InvalidRound, AlreadyProposed):
            pass

    async def receive_vote(self, vote: Vote):
        try:
            await self._receive_vote(vote)
        except (InvalidEpoch, InvalidRound, AlreadyVoted):
            pass

    async def _receive_data(self, data: Data):
        self._verify_acceptable_data(data)

        self._messages.add_data(data)
        await self._election.receive_data(data)
        await self._receive_votes_if_exist(data)

    async def _receive_vote(self, vote: Vote):
        self._verify_acceptable_vote(vote)

        self._messages.add_vote(vote)
        await self._receive_vote_if_data_exist(vote)
        await self._raise_lazy_votes_if_available()

    async def _raise_receive_data(self, delay: float, data: Data):
        event = ReceiveDataEvent(data)
        event.deterministic = False

        mediator = self._event_system.get_mediator(DelayedEventMediator)
        mediator.execute(delay, event)

    async def _raise_receive_vote(self, delay: float, vote: Vote):
        event = ReceiveVoteEvent(vote)
        event.deterministic = False

        mediator = self._event_system.get_mediator(DelayedEventMediator)
        mediator.execute(delay, event)

    async def _raise_lazy_votes_if_available(self):
        if self._vote_timeout_started:
            return
        if not self._messages.reach_quorum(self._epoch.quorum_num):
            return
        if self._messages.reach_quorum_consensus(self._epoch.quorum_num):
            return

        self._vote_timeout_started = True
        for voter in self._epoch.get_voters_id():
            vote = self._vote_factory.create_lazy_vote(voter, self._epoch.num, self._num)
            await self._raise_receive_vote(delay=TIMEOUT_VOTE, vote=vote)

    async def _new_unreal_datums(self):
        none_data = self._data_factory.create_none_data(epoch_num=self._epoch.num,
                                                        round_num=self._num,
                                                        proposer_id=self._epoch.get_proposer_id(self._num))
        # NoneData must be received before RoundStart
        await self._receive_data(none_data)

        expected_proposer = self._epoch.get_proposer_id(self._num)
        lazy_data = self._data_factory.create_lazy_data(self._epoch.num,
                                                        self._num,
                                                        expected_proposer)
        await self._raise_receive_data(delay=TIMEOUT_PROPOSE, data=lazy_data)

    async def _receive_votes_if_exist(self, data: Data):
        votes_by_data_id = self._messages.get_votes(data_id=data.id)
        for vote in votes_by_data_id.values():
            await self._election.receive_vote(vote)

    async def _receive_vote_if_data_exist(self, vote: Vote):
        if self._messages.get_data(vote.data_id):
            await self._election.receive_vote(vote)

    def _verify_acceptable_data(self, data: Data):
        if self._epoch.num != data.epoch_num:
            raise InvalidEpoch(data.epoch_num, self._epoch.num)
        if self._num != data.round_num:
            raise InvalidRound(data.epoch_num, data.round_num, self._epoch.num, self._num)
        if data in self._messages:
            raise AlreadyProposed(data.id, data.proposer_id)

    def _verify_acceptable_vote(self, vote: Vote):
        if self._epoch.num != vote.epoch_num:
            raise InvalidEpoch(vote.epoch_num, self._epoch.num)
        if self._num != vote.round_num:
            raise InvalidRound(vote.epoch_num, vote.round_num, self._epoch.num, self._num)
        if vote in self._messages:
            raise AlreadyVoted(vote.id, vote.voter_id)

    def is_newer_than(self, epoch_num: int, round_num: int):
        return (self.epoch_num, self.num) > (epoch_num, round_num)

    def is_older_than(self, epoch_num: int, round_num: int):
        return (self.epoch_num, self.num) < (epoch_num, round_num)

    def is_equal_to(self, epoch_num: int, round_num: int):
        return (self.epoch_num, self.num) == (epoch_num, round_num)

    def __gt__(self, other: 'Round'):
        if not isinstance(other, Round):
            return False
        return self.is_newer_than(other.epoch_num, other.num)

    def __lt__(self, other: 'Round'):
        if not isinstance(other, Round):
            return False
        return self.is_older_than(other.epoch_num, other.num)


Datums = OrderedDict[bytes, Data]

Votes = OrderedDict[bytes, Vote]
VotesByDataID = DefaultDict[bytes, OrderedDict[bytes, Vote]]

Voters = Set[bytes]
VotersByDataID = DefaultDict[bytes, Set[bytes]]


class RoundMessages:
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


class RoundPool:
    def __init__(self):
        self._rounds: List[Round] = []

    @property
    def rounds(self) -> Sequence[Round]:
        return self._rounds

    def first_round(self):
        return self._rounds[0]

    def add_round(self, round_: Round):
        insort(self._rounds, round_)

    def get_round(self, epoch_num: int, round_num: int):
        try:
            return next(round_ for round_ in self._rounds
                        if round_.epoch_num == epoch_num and round_.num == round_num)
        except StopIteration:
            raise KeyError(epoch_num, round_num)

    def prune_round(self, latest_epoch_num: int, latest_round_num: int):
        self._rounds = [round_ for round_ in self._rounds
                        if (round_.is_newer_than(latest_epoch_num, latest_round_num) or
                            round_.is_equal_to(latest_epoch_num, latest_round_num))]

    def change_candidate(self, commit_id: bytes):
        candidate_round = self.first_round()
        candidate_round.candidate_id = commit_id
        for round_ in self._rounds[1:]:
            round_.candidate_id = candidate_round.result_id
