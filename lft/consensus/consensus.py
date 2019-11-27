from typing import TYPE_CHECKING, Sequence, List

from lft.event import EventRegister
from lft.consensus.messages.data import DataPool
from lft.consensus.messages.vote import VotePool
from lft.consensus.round import Round
from lft.consensus.events import InitializeEvent, RoundStartEvent, ReceiveDataEvent, ReceiveVoteEvent, RoundEndEvent
from lft.consensus.exceptions import InvalidRound

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
        self._data_pool = DataPool()
        self._vote_pool = VotePool()
        self._rounds: List[Round] = []

    async def _on_event_initialize(self, event: InitializeEvent):
        await self.initialize(event.term, event.round_num, event.candidate_data, event.votes)

    async def _on_event_round_start(self, event: RoundStartEvent):
        await self.round_start(event.term, event.round_num)

    async def _on_event_round_end(self, event: RoundEndEvent):
        await self.round_end(event.is_success, event.term_num, event.round_num)

    async def _on_event_receive_data(self, event: ReceiveDataEvent):
        await self.receive_data(event.data)

    async def _on_event_receive_vote(self, event: ReceiveVoteEvent):
        await self.receive_vote(event.vote)

    async def initialize(self, new_term: 'Term', new_round_num: int, candidate_data: 'Data', votes: Sequence['Vote']):
        assert not self._rounds

        new_round = Round(self._event_system, self._node_id, self._data_factory, self._vote_factory)
        await new_round.initialize(new_term, new_round_num, candidate_data, votes)
        self._rounds.append(new_round)

    async def round_start(self, new_term: 'Term', new_round_num: int):
        assert self._rounds

        last_round = self._rounds[-1]
        assert ((new_term.num == last_round.term_num and last_round.num + 1 == new_round_num) or
                (new_term.num == last_round.term_num + 1 and new_round_num == 0))

        candidate_round = self._rounds[0]

        new_round = Round(self._event_system, self._node_id, self._data_factory, self._vote_factory)
        await new_round.initialize(new_term, new_round_num,
                                   candidate_round.candidate.data, candidate_round.candidate.votes)
        await new_round.round_start(new_term, new_round_num)
        self._rounds.append(new_round)

        await self._receive_round_messages(new_term.num, new_round_num)

    async def round_end(self, is_success: bool, term_num: int, round_num: int):
        if is_success:
            self._trim_round(term_num, round_num)

    async def receive_data(self, data: 'Data'):
        for prev_vote in data.prev_votes:
            if prev_vote:
                await self.receive_vote(prev_vote)

        try:
            self._verify_acceptable_message(data)
        except InvalidRound:
            pass
        try:
            round_ = self._get_round(data.term_num, data.round_num)
        except InvalidRound:
            self._data_pool.add_data(data)
        else:
            await round_.receive_data(data)

    async def receive_vote(self, vote: 'Vote'):
        try:
            self._verify_acceptable_message(vote)
        except InvalidRound:
            pass
        try:
            round_ = self._get_round(vote.term_num, vote.round_num)
        except InvalidRound:
            self._vote_pool.add_vote(vote)
        else:
            await round_.receive_vote(vote)

    def _verify_acceptable_message(self, message: 'Message'):
        # To avoid MMO attack, app must prevent to receive newer messages than current round's.
        # To get the messages at the round of messages the app has to gossip.

        candidate_round = self._rounds[0]
        if candidate_round.is_newer_than(message.term_num, message.round_num):
            raise InvalidRound(message.term_num, message.round_num, candidate_round.term_num, candidate_round.num)

    def _get_round(self, term_num: int, round_num: int):
        try:
            return next(round_ for round_ in self._rounds
                        if round_.term_num == term_num and round_.num == round_num)
        except StopIteration:
            raise InvalidRound(term_num, round_num, -1, -1)

    def _trim_round(self, latest_term_num: int, latest_round_num: int):
        self._rounds = [round_ for round_ in self._rounds
                        if (round_.is_newer_than(latest_term_num, latest_round_num) or
                            round_.is_equal_to(latest_term_num, latest_round_num))]
        self._data_pool.trim(latest_term_num, latest_round_num)
        self._vote_pool.trim(latest_term_num, latest_round_num)

    async def _receive_round_messages(self, term_num: int, round_num: int):
        for data in self._data_pool.get_datums(term_num, round_num):
            await self.receive_data(data)
        for vote in self._vote_pool.get_votes(term_num, round_num):
            await self.receive_vote(vote)

    _handler_prototypes = {
        InitializeEvent: _on_event_initialize,
        RoundStartEvent: _on_event_round_start,
        RoundEndEvent: _on_event_round_end,
        ReceiveDataEvent: _on_event_receive_data,
        ReceiveVoteEvent: _on_event_receive_vote,
    }



