from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Sequence

from lft.event import EventRegister
from lft.consensus.term import TermPool
from lft.consensus.messages.data import DataPool
from lft.consensus.messages.vote import VotePool
from lft.consensus.round import Round, RoundPool
from lft.consensus.events import InitializeEvent, RoundStartEvent, ReceiveDataEvent, ReceiveVoteEvent
from lft.consensus.exceptions import InvalidRound, InvalidTerm, InvalidProposer, InvalidVoter

if TYPE_CHECKING:
    from lft.event import EventSystem
    from lft.consensus.term import Term
    from lft.consensus.messages.data import Data, DataFactory
    from lft.consensus.messages.vote import Vote, VoteFactory
    from lft.consensus.messages.message import Message


class Consensus(EventRegister):
    def __init__(self, event_system: 'EventSystem', node_id: bytes,
                 data_factory: 'DataFactory', vote_factory: 'VoteFactory'):
        super().__init__(event_system.simulator)

        self._event_system = event_system
        self._node_id = node_id
        self._data_factory = data_factory
        self._vote_factory = vote_factory

        self._term_pool = TermPool()
        self._round_pool = RoundPool()
        self._data_pool = DataPool()
        self._vote_pool = VotePool()

    async def _on_event_initialize(self, event: InitializeEvent):
        await self.initialize(event.prev_term, event.term, event.round_num, event.candidate_data, event.candidate_votes)

    async def _on_event_round_start(self, event: RoundStartEvent):
        await self.round_start(event.term, event.round_num)

    async def _on_event_receive_data(self, event: ReceiveDataEvent):
        await self.receive_data(event.data)

    async def _on_event_receive_vote(self, event: ReceiveVoteEvent):
        await self.receive_vote(event.vote)

    async def initialize(self, prev_term: 'Term', new_term: 'Term', new_round_num: int,
                         candidate_data: 'Data', candidate_votes: Sequence['Vote']):
        self._term_pool.add_term(prev_term)
        self._term_pool.add_term(new_term)
        self._data_pool.add_data(candidate_data)
        for candidate_vote in candidate_votes:
            self._vote_pool.add_vote(candidate_vote)

        new_round = self._new_round(new_term, new_round_num, candidate_data.id)
        await new_round.round_start()

    async def round_start(self, new_term: 'Term', new_round_num: int):
        self._term_pool.add_term(new_term)

        new_round = self._new_or_get_round(new_term.num, new_round_num)
        await new_round.round_start()

        candidate_data = self._data_pool.get_data(new_round.candidate_id)
        self._trim_messages(candidate_data.term_num, candidate_data.round_num)

    async def receive_data(self, data: 'Data'):
        for prev_vote in data.prev_votes:
            if prev_vote:
                await self.receive_vote(prev_vote)

        try:
            self._verify_acceptable_data(data)
        except (InvalidTerm, InvalidRound, InvalidProposer):
            return
        self._data_pool.add_data(data)

        round_ = self._new_or_get_round(data.term_num, data.round_num)
        if data.is_not():
            await round_.receive_data(data)
        else:
            if round_.candidate_id == data.prev_id:
                async with self._try_change_candidate(round_):
                    await round_.receive_data(data)

    async def receive_vote(self, vote: 'Vote'):
        try:
            self._verify_acceptable_vote(vote)
        except (InvalidTerm, InvalidRound, InvalidVoter):
            return
        self._vote_pool.add_vote(vote)

        round_ = self._new_or_get_round(vote.term_num, vote.round_num)
        async with self._try_change_candidate(round_):
            await round_.receive_vote(vote)

    def _verify_acceptable_message(self, message: 'Message'):
        # To avoid MMO attack, app must prevent to receive newer messages than current round's.
        # To get the messages at the round of messages the app has to gossip.

        candidate_round = self._round_pool.first_round()
        if candidate_round.is_newer_than(message.term_num, message.round_num):
            raise InvalidRound(message.term_num, message.round_num, candidate_round.term_num, candidate_round.num)

        if candidate_round.term_num + 1 < message.term_num:
            raise InvalidTerm(message.term_num, candidate_round.term_num)

        if candidate_round.term_num + 1 == message.term_num:
            if message.round_num > 0:
                raise InvalidTerm(message.term_num, candidate_round.term_num)

    def _verify_acceptable_data(self, data: 'Data'):
        self._verify_acceptable_message(data)
        term = self._term_pool.get_term(data.term_num)
        term.verify_proposer(data.proposer_id, data.round_num)

    def _verify_acceptable_vote(self, vote: 'Vote'):
        self._verify_acceptable_message(vote)
        term = self._term_pool.get_term(vote.term_num)
        term.verify_voter(vote.voter_id)

    def _new_round(self, term: 'Term', round_num: int, candidate_id: bytes):
        new_round = Round(self._event_system, self._node_id, term, round_num,
                          self._data_factory, self._vote_factory, self._data_pool, self._vote_pool)
        new_round.candidate_id = candidate_id
        self._round_pool.add_round(new_round)
        return new_round

    def _new_or_get_round(self, term_num: int, round_num: int):
        try:
            return self._round_pool.get_round(term_num, round_num)
        except KeyError:
            try:
                term = self._term_pool.get_term(term_num)
            except KeyError:
                raise KeyError(term_num, round_num)
            else:
                candidate_round = self._round_pool.first_round()
                round_ = self._new_round(term, round_num, candidate_round.result_id)
                return round_

    def _trim_round(self, latest_term_num: int, latest_round_num: int):
        self._term_pool.trim_term(latest_term_num - 1)  # Need prev term
        self._round_pool.trim_round(latest_term_num, latest_round_num)

    def _trim_messages(self, latest_term_num: int, latest_round_num: int):
        self._data_pool.trim(latest_term_num, latest_round_num)
        self._vote_pool.trim(latest_term_num, latest_round_num)

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

            self._trim_round(target_round.term_num, target_round.num)
            self._round_pool.change_candidate()

            datums = self._data_pool.get_datums_connected(target_round.result_id)
            for data in datums:
                round_ = self._new_or_get_round(data.term_num, data.round_num)
                async with self._try_change_candidate(round_):
                    await self.receive_data(data)

    _handler_prototypes = {
        InitializeEvent: _on_event_initialize,
        RoundStartEvent: _on_event_round_start,
        ReceiveDataEvent: _on_event_receive_data,
        ReceiveVoteEvent: _on_event_receive_vote,
    }
