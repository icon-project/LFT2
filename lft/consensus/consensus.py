import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Sequence

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
        await self.initialize(event.prev_epoch, event.epoch, event.round_num, event.candidate_data, event.candidate_votes)

    async def _on_event_round_start(self, event: RoundStartEvent):
        await self.round_start(event.epoch, event.round_num)

    async def _on_event_receive_data(self, event: ReceiveDataEvent):
        await self.receive_data(event.data)

    async def _on_event_receive_vote(self, event: ReceiveVoteEvent):
        await self.receive_vote(event.vote)

    async def initialize(self, prev_epoch: 'Epoch', new_epoch: 'Epoch', new_round_num: int,
                         candidate_data: 'Data', candidate_votes: Sequence['Vote']):
        self._epoch_pool.add_epoch(prev_epoch)
        self._epoch_pool.add_epoch(new_epoch)
        self._data_pool.add_data(candidate_data)
        for candidate_vote in candidate_votes:
            self._vote_pool.add_vote(candidate_vote)

        new_round = self._new_round(new_epoch, new_round_num, candidate_data.id)
        await new_round.round_start()

    async def round_start(self, new_epoch: 'Epoch', new_round_num: int):
        if self._round_pool.first_round().is_newer_than(new_epoch.num, new_round_num):
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
        await self._receive_data_and_change_candidate_if_available(data)

    async def receive_vote(self, vote: 'Vote'):
        try:
            self._verify_acceptable_vote(vote)
        except (InvalidEpoch, InvalidRound, InvalidVoter):
            return
        self._vote_pool.add_vote(vote)
        await self._receive_vote_and_change_candidate_if_available(vote)

    async def _receive_prev_votes(self, data: 'Data'):
        for prev_vote in data.prev_votes:
            if prev_vote:
                await self.receive_vote(prev_vote)

    async def _receive_data_and_change_candidate_if_available(self, data: 'Data'):
        round_ = self._new_or_get_round(data.epoch_num, data.round_num)
        if data.is_lazy():
            await round_.receive_data(data)
        else:
            if round_.candidate_id == data.prev_id:
                async with self._try_change_candidate(round_):
                    await round_.receive_data(data)

    async def _receive_vote_and_change_candidate_if_available(self, vote: 'Vote'):
        round_ = self._new_or_get_round(vote.epoch_num, vote.round_num)
        async with self._try_change_candidate(round_):
            await round_.receive_vote(vote)

    def _verify_acceptable_message(self, message: 'Message'):
        # To avoid MMO attack, app must prevent to receive newer messages than current round's.
        # To get the messages at the round of messages the app has to gossip.

        candidate_round = self._round_pool.first_round()
        if candidate_round.is_newer_than(message.epoch_num, message.round_num):
            raise InvalidRound(message.epoch_num, message.round_num, candidate_round.epoch_num, candidate_round.num)

        if candidate_round.epoch_num + 1 < message.epoch_num:
            raise InvalidEpoch(message.epoch_num, candidate_round.epoch_num)

        if candidate_round.epoch_num + 1 == message.epoch_num:
            if message.round_num > 0:
                raise InvalidEpoch(message.epoch_num, candidate_round.epoch_num)

    def _verify_acceptable_data(self, data: 'Data'):
        self._verify_acceptable_message(data)
        epoch = self._get_epoch(data.epoch_num)
        epoch.verify_proposer(data.proposer_id, data.round_num)

    def _verify_acceptable_vote(self, vote: 'Vote'):
        self._verify_acceptable_message(vote)
        epoch = self._get_epoch(vote.epoch_num)
        epoch.verify_voter(vote.voter_id)

    def _get_epoch(self, epoch_num: int):
        try:
            epoch = self._epoch_pool.get_epoch(epoch_num)
        except KeyError:
            raise InvalidEpoch(epoch_num, self._round_pool.first_round().epoch_num)
        return epoch

    def _new_round(self, epoch: 'Epoch', round_num: int, candidate_id: bytes):
        election = Election(self._node_id, epoch, round_num, self._event_system,
                            self._data_factory, self._vote_factory, self._data_pool, self._vote_pool)
        new_round = Round(election, self._node_id, epoch, round_num,
                          self._event_system, self._data_factory, self._vote_factory)
        new_round.candidate_id = candidate_id
        self._round_pool.add_round(new_round)
        return new_round

    def _new_or_get_round(self, epoch_num: int, round_num: int):
        try:
            return self._round_pool.get_round(epoch_num, round_num)
        except KeyError:
            try:
                epoch = self._epoch_pool.get_epoch(epoch_num)
            except KeyError:
                raise KeyError(epoch_num, round_num)
            else:
                candidate_round = self._round_pool.first_round()
                round_ = self._new_round(epoch, round_num, candidate_round.result_id)
                return round_

    def _prune_round(self, latest_epoch_num: int, latest_round_num: int):
        self._epoch_pool.prune_epoch(latest_epoch_num - 1)  # Need prev epoch
        self._round_pool.prune_round(latest_epoch_num, latest_round_num)

    def _prune_messages(self, latest_epoch_num: int, latest_round_num: int):
        self._data_pool.prune_data(latest_epoch_num, latest_round_num)
        self._vote_pool.prune_vote(latest_epoch_num, latest_round_num)

    @asynccontextmanager
    async def _try_change_candidate(self, target_round: Round):
        old_result_id = target_round.result_id
        try:
            yield
        finally:
            if old_result_id == target_round.result_id:
                return
            if target_round.result_id is None:
                return

            self._prune_round(target_round.epoch_num, target_round.num)
            self._round_pool.change_candidate()

            new_candidate_data = self._data_pool.get_data(target_round.result_id)
            new_commit_data = self._data_pool.get_data(new_candidate_data.prev_id)
            self._prune_messages(new_commit_data.epoch_num, new_commit_data.round_num)

            datums = self._data_pool.get_datums_connected(target_round.result_id)
            for data in datums:
                round_ = self._new_or_get_round(data.epoch_num, data.round_num)
                async with self._try_change_candidate(round_):
                    await self.receive_data(data)

    _handler_prototypes = {
        InitializeEvent: _on_event_initialize,
        RoundStartEvent: _on_event_round_start,
        ReceiveDataEvent: _on_event_receive_data,
        ReceiveVoteEvent: _on_event_receive_vote,
    }
