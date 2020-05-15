import logging
from collections import Counter
from typing import DefaultDict, OrderedDict, Set, Optional, Dict
from lft.consensus.epoch import EpochPool
from lft.consensus.messages.data import Data, DataFactory, DataPool, DataVerifier
from lft.consensus.messages.vote import Vote, VoteFactory, VotePool
from lft.consensus.events import (RoundEndEvent, BroadcastDataEvent, BroadcastVoteEvent,
                                  ReceiveDataEvent, ReceiveVoteEvent)
from lft.consensus.epoch import Epoch
from lft.consensus.exceptions import InvalidProposer
from lft.event import EventSystem

__all__ = ("Election", "ElectionMessages")


class Election:
    def __init__(self,
                 node_id: bytes,
                 epoch_num: int,
                 round_num: int,
                 event_system: EventSystem,
                 data_factory: DataFactory,
                 vote_factory: VoteFactory,
                 epoch_pool: EpochPool,
                 data_pool: DataPool,
                 vote_pool: VotePool):
        self._node_id: bytes = node_id
        self._epoch = epoch_pool.get_epoch(epoch_num)
        self._round_num = round_num

        self._event_system: EventSystem = event_system
        self._data_factory: DataFactory = data_factory
        self._vote_factory: VoteFactory = vote_factory

        self._epoch_pool = epoch_pool
        self._data_pool = data_pool
        self._vote_pool = vote_pool

        self._logger = logging.getLogger(node_id.hex())

        self._data_verifier: DataVerifier = None

        self._candidate_id: bytes = None
        self._messages: ElectionMessages = ElectionMessages(self._epoch, round_num, data_factory)

        self._is_proposed = False
        self._is_voted = False

        self._is_ended = False
        self._is_started = False

    @property
    def result_id(self):
        result = self._messages.result
        if result and result.is_real():
            return result.id
        else:
            return None

    async def round_start(self):
        self._is_started = True
        self._data_verifier = await self._data_factory.create_data_verifier()

        await self._new_unreal_datums()
        await self._new_real_data_if_proposer()
        await self._vote_if_real_data_exist()

    async def receive_data(self, data: Data):
        if data.is_real() and data.proposer_id == self._node_id:
            self._is_proposed = True

        self._messages.add_data(data)
        await self._update_result()
        await self._vote_if_available(data)

    async def receive_vote(self, vote: Vote):
        if vote.is_real() and vote.voter_id == self._node_id:
            self._is_voted = True

        self._messages.add_vote(vote)
        await self._update_result()

    async def _raise_broadcast_data(self, data):
        self._event_system.simulator.raise_event(
            BroadcastDataEvent(
                data=data
            )
        )
        self._event_system.simulator.raise_event(
            ReceiveDataEvent(
                data=data
            )
        )

    async def _raise_broadcast_vote(self, vote: Vote):
        self._event_system.simulator.raise_event(
            BroadcastVoteEvent(
                vote=vote)
        )
        self._event_system.simulator.raise_event(
            ReceiveVoteEvent(
                vote=vote
            )
        )

    async def _raise_round_end(self, result: Data):
        if result.is_real():
            new_candidate = result
            round_end = RoundEndEvent(
                is_success=True,
                epoch_num=self._epoch.num,
                round_num=self._round_num,
                candidate_id=new_candidate.id,
                commit_id=new_candidate.prev_id
            )
        else:
            round_end = RoundEndEvent(
                is_success=False,
                epoch_num=self._epoch.num,
                round_num=self._round_num,
                candidate_id=None,
                commit_id=None
            )
        self._event_system.simulator.raise_event(round_end)

    async def _new_unreal_datums(self):
        none_data = self._data_factory.create_none_data(epoch_num=self._epoch.num,
                                                        round_num=self._round_num,
                                                        proposer_id=self._epoch.get_proposer_id(self._round_num))
        self._messages.add_data(none_data)

        lazy_data = self._data_factory.create_lazy_data(epoch_num=self._epoch.num,
                                                        round_num=self._round_num,
                                                        proposer_id=self._epoch.get_proposer_id(self._round_num))
        self._messages.add_data(lazy_data)

    async def _new_real_data_if_proposer(self):
        if self._is_proposed:
            return

        try:
            self._epoch.verify_proposer(self._node_id, self._round_num)
        except InvalidProposer:
            return

        candidate_data = self._data_pool.get_data(self._candidate_id)

        candidate_epoch_num = candidate_data.epoch_num
        candidate_round_num = candidate_data.round_num

        candidate_epoch = self._epoch_pool.get_epoch(candidate_data.epoch_num)
        if candidate_epoch.quorum_num == 0:
            consensus_votes = tuple()
        else:
            candidate_votes = self._vote_pool.get_votes(candidate_epoch_num, candidate_round_num)
            candidate_votes = {vote.voter_id: vote
                               for vote in candidate_votes
                               if vote.data_id == self._candidate_id}

            candidate_votes = {voter: candidate_votes[voter]
                               for voter in candidate_epoch.voters
                               if voter in candidate_votes}

            consensus_id_counter = Counter(vote.consensus_id for vote in candidate_votes.values())
            consensus_id = consensus_id_counter.most_common(1)[0][0]

            consensus_votes = tuple(
                candidate_votes[voter]
                if voter in candidate_votes and candidate_votes[voter].consensus_id == consensus_id else
                self._vote_factory.create_lazy_vote(voter, candidate_epoch_num, candidate_round_num)
                for voter in candidate_epoch.voters
            )

        new_data = await self._data_factory.create_data(
            data_number=candidate_data.number + 1,
            prev_id=self._candidate_id,
            epoch_num=self._epoch.num,
            round_num=self._round_num,
            prev_votes=consensus_votes
        )
        await self._raise_broadcast_data(new_data)
        self._is_proposed = True

    async def _update_result(self):
        if not self._messages.result or not self._messages.result.is_determinative():
            self._messages.update()
        if not self._messages.result:
            return

        if self._is_ended:
            return
        await self._raise_round_end(self._messages.result)
        self._is_ended = self._messages.result and self._messages.result.is_determinative()

    async def _vote_if_real_data_exist(self):
        first_real_data = self._messages.first_real_data
        if first_real_data:
            await self._verify_and_broadcast_vote(first_real_data)
            await self._update_result()
            self._is_voted = True

    async def _vote_if_available(self, data: Data):
        if not self._is_started:
            return
        if self._is_ended:
            return
        if self._is_voted:
            return

        await self._verify_and_broadcast_vote(data)
        self._is_voted = True

    async def _verify_and_broadcast_vote(self, data):
        if await self._verify_data(data):
            vote = await self._vote_factory.create_vote(data_id=data.id,
                                                        commit_id=self._candidate_id,
                                                        epoch_num=self._epoch.num,
                                                        round_num=self._round_num)
        else:
            vote = self._vote_factory.create_none_vote(epoch_num=self._epoch.num,
                                                       round_num=self._round_num)
        await self._raise_broadcast_vote(vote)

    async def _verify_data(self, data):
        if self._candidate_id != data.prev_id:
            return False
        candidate_data = self._data_pool.get_data(self._candidate_id)
        if candidate_data.number + 1 != data.number:
            return False
        if data.is_lazy():
            return False
        try:
            await self._data_verifier.verify(candidate_data, data)
        except Exception as e:
            return False
        else:
            return True


# dict[data_id] = data
Datums = OrderedDict[bytes, Data]

# dict[data_id][consensus_id][voter_id] = vote
Votes = DefaultDict[bytes, DefaultDict[bytes, Dict[bytes, Vote]]]


class ElectionMessages:
    def __init__(self, epoch: Epoch, round_num: int, data_factory: DataFactory):
        self._epoch = epoch
        self._round_num = round_num
        self._data_factory = data_factory

        self._datums: Datums = OrderedDict()
        self._votes: Votes = DefaultDict(lambda : DefaultDict(dict))

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
        self._votes[vote.data_id][vote.consensus_id][vote.voter_id] = vote

    def update(self):
        # RealData : Determine round success and round end
        # NoneData : Determine round failure and round end
        # LazyData : Cannot determine but round end
        # None : Nothing changes

        if self._update_quorum_data():
            return

        if self._update_lazy_data():
            return

        self._result = None

    def _update_quorum_data(self):
        quorum_datums = []
        for data in self._datums.values():
            consensus_id_to_votes = self._votes[data.id]
            if self._epoch.quorum_num == 0:  # genesis
                quorum_datums.append(data)
            else:
                if any(len(votes) >= self._epoch.quorum_num
                       for votes in consensus_id_to_votes.values()):
                    quorum_datums.append(data)

        quorum_datums.sort(key=lambda d: not d.is_determinative())
        assert ((len(quorum_datums) <= 1) or
                (len(quorum_datums) == 2 and quorum_datums[0].is_determinative() and quorum_datums[1].is_lazy()))

        if quorum_datums and quorum_datums[0].is_determinative():
            self._result = quorum_datums[0]
            return True
        return False

    def _update_lazy_data(self):
        assert len(self._voters) <= len(self._epoch.voters)
        if len(self._voters) == len(self._epoch.voters):
            self._result = self._find_lazy_data()
            return True
        return False

    def _find_lazy_data(self):
        try:
            return next(data for data in self._datums.values() if data.is_lazy())
        except StopIteration:
            proposer_id = self._epoch.get_proposer_id(self._round_num)
            return self._data_factory.create_lazy_data(self._epoch.num, self._round_num, proposer_id)

