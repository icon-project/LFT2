import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Iterable, Optional
from lft.event import EventRegister
from lft.consensus.epoch import EpochPool
from lft.consensus.messages.data import DataPool
from lft.consensus.messages.vote import VotePool
from lft.consensus.round import Round, RoundPool
from lft.consensus.election import Election
from lft.consensus.events import InitializeEvent, RoundStartEvent, ReceiveDataEvent, ReceiveVoteEvent
from lft.consensus.exceptions import InvalidRound, InvalidEpoch, InvalidProposer, InvalidVoter

if TYPE_CHECKING:
    from lft.event import EventSystem
    from lft.consensus.epoch import Epoch
    from lft.consensus.messages.data import Data, DataFactory
    from lft.consensus.messages.vote import Vote, VoteFactory
    from lft.consensus.messages.message import Message

__all__ = ("Consensus", )


class Consensus(EventRegister):
    def __init__(self, event_system: 'EventSystem', node_id: bytes,
                 data_factory: 'DataFactory', vote_factory: 'VoteFactory'):
        super().__init__(event_system.simulator)

        self._event_system = event_system
        self._node_id = node_id
        self._data_factory = data_factory
        self._vote_factory = vote_factory

        self._epoch_pool = EpochPool()
        self._round_pool = RoundPool()
        self._data_pool = DataPool()
        self._vote_pool = VotePool()

        self._logger = logging.getLogger(node_id.hex())

    async def _on_event_initialize(self, event: InitializeEvent):
        await self.initialize(event.commit_id, event.epoch_pool, event.data_pool, event.vote_pool)

    async def _on_event_round_start(self, event: RoundStartEvent):
        await self.round_start(event.epoch, event.round_num)

    async def _on_event_receive_data(self, event: ReceiveDataEvent):
        await self.receive_data(event.data)

    async def _on_event_receive_vote(self, event: ReceiveVoteEvent):
        await self.receive_vote(event.vote)

    async def initialize(self, commit_id: bytes,
                         epoch_pool: Iterable['Epoch'], data_pool: Iterable['Data'], vote_pool: Iterable['Vote']):
        for epoch in epoch_pool:
            self._epoch_pool.add_epoch(epoch)

        for data in data_pool:
            if data.id == commit_id:
                self._data_pool.add_data(data)
            else:
                self._new_round(data.epoch_num, data.round_num, commit_id)

        for round_ in self._round_pool.rounds:
            datums = (data for data in data_pool
                      if data.epoch_num == round_.epoch_num
                      if data.round_num == round_.num)
            for data in datums:
                await self.receive_data(data)

            votes = (vote for vote in vote_pool
                     if vote.epoch_num == round_.epoch_num
                     if vote.round_num == round_.num)
            for vote in votes:
                await self.receive_vote(vote)

    async def round_start(self, new_epoch: 'Epoch', new_round_num: int):
        if self._get_candidate_round().is_newer_than(new_epoch.num, new_round_num):
            # Maybe sync
            return

        self._epoch_pool.add_epoch(new_epoch)

        new_round = self._new_or_get_round(new_epoch.num, new_round_num)
        await new_round.round_start()

    async def receive_data(self, data: 'Data'):
        await self._receive_prev_votes(data)

        try:
            self._verify_acceptable_data(data)
        except (InvalidEpoch, InvalidRound, InvalidProposer):
            return
        self._data_pool.add_data(data)

        try:
            self._verify_round_message(data)
        except InvalidRound:
            return
        await self._receive_data_and_change_candidate_if_available(data)

    async def receive_vote(self, vote: 'Vote'):
        try:
            self._verify_acceptable_vote(vote)
        except (InvalidEpoch, InvalidRound, InvalidVoter):
            return
        self._vote_pool.add_vote(vote)

        try:
            self._verify_round_message(vote)
        except InvalidRound:
            return
        await self._receive_vote_and_change_candidate_if_available(vote)

    async def _receive_prev_votes(self, data: 'Data'):
        for prev_vote in data.prev_votes:
            if prev_vote:
                await self.receive_vote(prev_vote)

    async def _receive_data_and_change_candidate_if_available(self, data: 'Data'):
        round_ = self._new_or_get_round(data.epoch_num, data.round_num)
        if data.is_real():
            if data.is_genesis() or data.prev_id in self._data_pool:
                async with self._try_change_candidate(round_, pruning_messages=True):
                    await round_.receive_data(data)
        else:
            await round_.receive_data(data)

    async def _receive_vote_and_change_candidate_if_available(self, vote: 'Vote'):
        round_ = self._new_or_get_round(vote.epoch_num, vote.round_num)
        if not vote.is_none() and not vote.is_lazy():
            async with self._try_change_candidate(round_, pruning_messages=True):
                await round_.receive_vote(vote)
        else:
            await round_.receive_vote(vote)

    def _verify_acceptable_message(self, message: 'Message'):
        # To avoid MMO attack, app must prevent to receive newer messages than current round's.
        # To get the messages at the round of messages the app has to gossip.

        candidate_round = self._get_candidate_round()
        if candidate_round.epoch_num != 0 or candidate_round.num != 0:
            # Genesis Data does not have commit data
            commit_id = candidate_round.candidate_id
            commit_data = self._data_pool.get_data(commit_id)
            if (message.epoch_num, message.round_num) <= (commit_data.epoch_num, commit_data.round_num):
                raise InvalidRound(message.epoch_num, message.round_num, commit_data.epoch_num, commit_data.round_num)

        if candidate_round.epoch_num + 1 < message.epoch_num:
            raise InvalidEpoch(message.epoch_num, candidate_round.epoch_num)

        # This condition cannot cover that round 0 of new epoch is timeout round
        # if candidate_round.epoch_num + 1 == message.epoch_num:
        #     if message.round_num > 0:
        #         raise InvalidEpoch(message.epoch_num, candidate_round.epoch_num)

    def _verify_acceptable_data(self, data: 'Data'):
        self._verify_acceptable_message(data)
        epoch = self._get_epoch(data.epoch_num)
        epoch.verify_proposer(data.proposer_id, data.round_num)

    def _verify_acceptable_vote(self, vote: 'Vote'):
        self._verify_acceptable_message(vote)
        epoch = self._get_epoch(vote.epoch_num)
        epoch.verify_voter(vote.voter_id)

    def _verify_round_message(self, message: 'Message'):
        candidate_round = self._get_candidate_round()
        if candidate_round.is_newer_than(message.epoch_num, message.round_num):
            raise InvalidRound(message.epoch_num, message.round_num, candidate_round.epoch_num, candidate_round.num)

    def _get_epoch(self, epoch_num: int):
        try:
            return self._epoch_pool.get_epoch(epoch_num)
        except KeyError:
            raise InvalidEpoch(epoch_num, self._get_candidate_round().epoch_num)

    def _new_round(self, epoch_num: int, round_num: int, candidate_id: bytes):
        epoch = self._get_epoch(epoch_num)
        election = Election(self._node_id, epoch.num, round_num, self._event_system,
                            self._data_factory, self._vote_factory, self._epoch_pool, self._data_pool, self._vote_pool)
        new_round = Round(election, self._node_id, epoch, round_num,
                          self._event_system, self._data_factory, self._vote_factory)
        new_round.candidate_id = candidate_id
        self._round_pool.add_round(new_round)
        return new_round

    def _new_or_get_round(self, epoch_num: int, round_num: int):
        try:
            return self._round_pool.get_round(epoch_num, round_num)
        except KeyError:
            candidate_round = self._get_candidate_round()
            round_ = self._new_round(epoch_num, round_num, candidate_round.result_id)
            return round_

    def _get_candidate_round(self):
        return self._round_pool.first_round()

    def _prune_round(self, latest_epoch_num: int, latest_round_num: int):
        self._epoch_pool.prune_epoch(latest_epoch_num - 1)  # Need prev epoch
        self._round_pool.prune_round(latest_epoch_num, latest_round_num)

    def _prune_messages(self, latest_epoch_num: int, latest_round_num: int):
        self._data_pool.prune_data(latest_epoch_num, latest_round_num)
        self._vote_pool.prune_vote(latest_epoch_num, latest_round_num)

    def _prune_messages_before_commit(self):
        candidate_round = self._get_candidate_round()
        candidate_data = self._data_pool.get_data(candidate_round.result_id)
        try:
            commit_data = self._data_pool.get_data(candidate_data.prev_id)
        except KeyError:
            # Already pruned
            pass
        else:
            self._prune_messages(commit_data.epoch_num, commit_data.round_num)

    @asynccontextmanager
    async def _try_change_candidate(self, target_round: Round, pruning_messages=False):
        is_candidate_changed = self._is_candidate_changed(target_round)
        try:
            yield
        finally:
            if is_candidate_changed():
                self._prune_round(target_round.epoch_num, target_round.num)
                await self._propagate_candidate_changed(target_round)
                await self._try_change_candidate_connected_datums(target_round.result_id)

                if pruning_messages:
                    self._prune_messages_before_commit()

    async def _try_change_candidate_connected_datums(self, prev_id: bytes):
        datums = self._data_pool.get_datums_connected(prev_id)
        for data in datums:
            round_ = self._new_or_get_round(data.epoch_num, data.round_num)
            async with self._try_change_candidate(round_):
                await self.receive_data(data)

    async def _propagate_candidate_changed(self, target_round: Round):
        candidate = self._data_pool.get_data(target_round.result_id)
        self._round_pool.change_candidate(candidate.prev_id)

    def _is_candidate_changed(self, target_round: Round):
        old_result_id = target_round.result_id

        def _checker():
            new_result_id = target_round.result_id
            if new_result_id is None:
                return False
            if new_result_id == old_result_id:
                return False
            return True
        return _checker

    _handler_prototypes = {
        InitializeEvent: _on_event_initialize,
        RoundStartEvent: _on_event_round_start,
        ReceiveDataEvent: _on_event_receive_data,
        ReceiveVoteEvent: _on_event_receive_vote,
    }
