import logging
from typing import Optional, Sequence, OrderedDict, Set, List, Dict

from collections import defaultdict

from lft.consensus.data import DataFactory, Data
from lft.consensus.events import InitializeEvent, StartRoundEvent, DoneRoundEvent, ReceivedDataEvent, ReceivedVoteEvent, \
    SyncRequestEvent
from lft.consensus.exceptions import InvalidTerm, InvalidProposer, InvalidRound, InvalidVoter, ReachCandidate, NeedSync
from lft.consensus.layers import SyncLayer, RoundLayer
from lft.consensus.term import Term
from lft.consensus.vote import VoteFactory, Vote
from lft.event import EventRegister, EventSystem


class OrderLayer(EventRegister):
    def __init__(self,
                 sync_layer: SyncLayer,
                 node_id: bytes,
                 event_system: EventSystem,
                 data_factory: DataFactory,
                 vote_factory: VoteFactory):
        super().__init__(event_system.simulator)
        self._sync_layer = sync_layer
        self._node_id = node_id
        self._event_system = event_system
        self._data_factory = data_factory
        self._vote_factory = vote_factory
        self._logger = logging.getLogger(node_id.hex())

        self._term: Optional[Term] = None
        self._datums: Datums = defaultdict(lambda: defaultdict(OrderedDict))
        self._votes: Votes = defaultdict(lambda: defaultdict(OrderedDict))
        self._message_container: MessageContainer = None

        self._round_num = -1

    async def _on_event_initialize(self, event: InitializeEvent):
        await self._initialize(
            term=event.term,
            round_num=event.round_num,
            candidate_data=event.candidate_data,
            votes=event.votes
        )

    async def _on_event_start_round(self, event: StartRoundEvent):
        await self._round_start(event.term, event.round_num)

    async def _on_event_received_data(self, event: ReceivedDataEvent):
        try:
            await self._receive_data(event.data)
        except (InvalidTerm, InvalidRound, InvalidProposer, InvalidVoter):
            pass

    async def _on_event_received_vote(self, event: ReceivedVoteEvent):
        try:
            await self._receive_vote(event.vote)
        except (InvalidTerm, InvalidRound, InvalidVoter):
            pass

    async def _on_event_done_round(self, event: DoneRoundEvent):
        if event.is_success:
            self._message_container.candidate_data = event.candidate_data
            await self._sync_layer.done_round(event.candidate_data)

    async def _initialize(self, term: Term, round_num: int, candidate_data: Data, votes: Sequence['Vote']):
        self._term = term
        self._round_num = round_num
        self._message_container = MessageContainer(term, candidate_data)

        await self._sync_layer.initialize(term, round_num, candidate_data, votes)

    async def _round_start(self, term: Term, round_num: int):
        self._verify_acceptable_start_round(term, round_num)

        self._term = term
        self._round_num = round_num
        await self._sync_layer.start_round(term, round_num)

        for data in self._get_datums(self._round_num):
            await self._sync_layer.receive_data(data)

        for vote in self._get_votes(self._round_num):
            await self._sync_layer.receive_vote(vote)

    async def _receive_data(self, data: Data):
        self._verify_acceptable_data(data)
        await self._save_and_pass_message(data)

    async def _receive_vote(self, vote: Vote):
        self._verify_acceptable_vote(vote)
        await self._save_and_pass_message(vote)

    async def _save_and_pass_message(self, message):
        try:
            if isinstance(message, Data):
                self._save_data(message)
            elif isinstance(message, Vote):
                self._save_vote(message)
        except ReachCandidate as e:
            await self._sync_layer.change_candidate(e.candidate, e.votes)
        except NeedSync as e:
            self._event_system.simulator.raise_event(
                SyncRequestEvent(e.old_candidate_id, e.new_candidate_id)
            )
        finally:
            if message.round_num == self._round_num:
                if isinstance(message, Data):
                    await self._sync_layer.receive_data(message)
                elif isinstance(message, Vote):
                    await self._sync_layer.receive_vote(message)

    def _verify_acceptable_start_round(self, term: Term, round_num: int):
        if term.num == self._term.num:
            if round_num != self._round_num + 1:
                raise InvalidRound(round_num, self._round_num)
        elif term.num == self._term.num + 1:
            if round_num != 0:
                raise InvalidRound(round_num, 0)
        else:
            raise InvalidTerm(term=term.num, expected=self._term.num)

    def _verify_acceptable_data(self, data: Data):
        self._verify_acceptable_round_message(data)
        if self._term.verify_proposer(data.proposer_id, data.round_num):
            raise InvalidProposer(data.proposer_id, self._term.get_proposer_id(data.round_num))

    def _verify_acceptable_round_message(self, message):
        if message.term_num != self._term.num:
            raise InvalidTerm(message.term_num, self._term.num)
        elif message.round_num < self._message_container.candidate_data.round_num:
            if message.term_num == self._message_container.candidate_data.term_num:
                raise InvalidRound(message.round_num, self._round_num)

    def _verify_acceptable_vote(self, vote: Vote):
        self._verify_acceptable_round_message(vote)
        if not (vote.voter_id in self._term.voters):
            raise InvalidVoter(vote.voter_id, b'')

    def _save_data(self, data: Data):
        self._message_container.add_data(data)

    def _save_vote(self, vote: Vote):
        self._message_container.add_vote(vote)

    def _get_datums(self, round_num: int) -> Sequence:
        return self._message_container.get_datums(round_num)

    def _get_votes(self, round_num: int) -> Sequence:
        return self._message_container.get_votes(round_num)

    _handler_prototypes = {
        InitializeEvent: _on_event_initialize,
        StartRoundEvent: _on_event_start_round,
        ReceivedDataEvent: _on_event_received_data,
        ReceivedVoteEvent: _on_event_received_vote,
        DoneRoundEvent: _on_event_done_round
    }


Datums = Dict[int, Dict[int, OrderedDict[bytes, Data]]]
Votes = Dict[int, Dict[int, OrderedDict[bytes, Data]]]


class MessageContainer:
    def __init__(self, term: Term, candidate_data: Data):
        self._term: Term = term
        self._old_term: Term = None
        self._candidate_data = candidate_data
        self._datums = defaultdict(OrderedDict)  # [round_num][data_id][data]
        self._votes = defaultdict(lambda: defaultdict(OrderedDict))  # [round_num][data_id][vote_id][vote]
        self._sync_request_datums = []

    @property
    def candidate_data(self) -> Data:
        return self._candidate_data

    @candidate_data.setter
    def candidate_data(self, candidate_data: Data):
        self._candidate_data = candidate_data
        for round_num in list(self._datums.keys()):
            if round_num < candidate_data.round_num:
                del self._datums[round_num]

        for round_num in list(self._votes.keys()):
            if round_num < candidate_data.round_num:
                del self._votes[round_num]

    @property
    def term(self) -> Term:
        return self._term

    @term.setter
    def term(self, term: Term):
        self._old_term = self.term
        self._term = term

    def add_vote(self, vote: Vote):
        if vote.term_num == self.candidate_data.term_num:
            if vote.round_num < self.candidate_data.round_num:
                return
        elif vote.term_num < self.candidate_data.term_num:
            return

        if vote.term_num == self._term.num:
            self._term.verify_vote(vote)
        elif vote.term_num == self._old_term.num:
            self._old_term.verify_vote(vote)
        else:
            return

        votes_has_same_data_id = self._votes[vote.round_num][vote.data_id]
        votes_has_same_data_id[vote.voter_id] = vote

        if len(votes_has_same_data_id) >= self.term.quorum_num and vote.data_id != self.candidate_data.id:
            try:
                data = self._datums[vote.round_num][vote.data_id]
            except KeyError:
                self._raise_need_sync(vote)
            else:
                if data.number == self.candidate_data.number or data.prev_id == self.candidate_data.id:
                    self.candidate_data = data
                    raise ReachCandidate(data, list(votes_has_same_data_id.values()))
                else:
                    self._raise_need_sync(vote)

    def _raise_need_sync(self, vote):
        if vote.data_id not in self._sync_request_datums:
            self._sync_request_datums.append(vote.data_id)
            raise NeedSync(self.candidate_data.id, vote.data_id)

    def add_data(self, data: Data):
        if data.term_num == self.candidate_data.term_num:
            if data.round_num < self.candidate_data.round_num:
                return
        elif data.term_num < self.candidate_data.term_num:
            return
        self._datums[data.round_num][data.id] = data
        for vote in data.prev_votes:
            self.add_vote(vote)

    def get_datums(self, round_num: int) -> Sequence:
        return self._datums[round_num].values()

    def get_votes(self, round_num: int) -> Sequence:
        round_votes = []
        for votes_by_data_id in self._votes[round_num].values():
            round_votes.extend(votes_by_data_id.values())
        return round_votes
