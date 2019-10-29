import logging
from typing import Sequence

from lft.consensus.round import Round, Candidate
from lft.consensus.data import Data, DataVerifier, DataFactory
from lft.consensus.vote import Vote, VoteVerifier, VoteFactory
from lft.consensus.events import (DoneRoundEvent, BroadcastDataEvent, BroadcastVoteEvent,
                                  ReceivedDataEvent, ReceivedVoteEvent)
from lft.consensus.term import Term, TermFactory
from lft.consensus.exceptions import InvalidProposer, AlreadyCompleted, AlreadyVoted, CannotComplete
from lft.event import EventSystem


class SyncLayer:
    def __init__(self, node_id: bytes, event_system: EventSystem, data_factory: DataFactory,
                 vote_factory: VoteFactory, term_factory: TermFactory):
        self._event_system: EventSystem = event_system
        self._data_factory: DataFactory = data_factory
        self._vote_factory: VoteFactory = vote_factory
        self._term_factory: TermFactory = term_factory
        self._logger = logging.getLogger(node_id.hex())

        self._data_verifier: DataVerifier = None
        self._vote_verifier: VoteVerifier = None

        self._candidate: Candidate = None
        self._round: Round = None
        self._term: Term = None
        self._node_id: bytes = node_id
        self._is_voted = False

    async def initialize(self, term_num: int, round_num: int, candidate_data: Data,
                         voters: Sequence[bytes], votes: Sequence[Vote]):
        self._data_verifier = await self._data_factory.create_data_verifier()
        self._vote_verifier = await self._vote_factory.create_vote_verifier()

        self._candidate = Candidate(
            data=candidate_data,
            votes=votes
        )
        await self._start_new_round(
            term_num=term_num,
            round_num=round_num,
            voters=voters
        )

    async def start_round(self, term_num: int, round_num: int, voters: Sequence[bytes]):
        if not self._is_next_round(term_num, round_num):
            return

        await self._start_new_round(
            term_num=term_num,
            round_num=round_num,
            voters=voters
        )
        self._is_voted = False

    async def propose_data(self, data: Data):
        try:
            self._round.add_data(data)
        except AlreadyCompleted:
            pass
        else:
            if not self._is_voted:
                await self._verify_and_broadcast_vote(data)
                self._is_voted = True

            await self._update_round_if_complete()

    async def vote_data(self, vote: Vote):
        try:
            self._round.add_vote(vote)
        except AlreadyCompleted:
            pass
        except AlreadyVoted:
            pass
        else:
            await self._update_round_if_complete()

    async def _update_round_if_complete(self):
        try:
            self._round.complete()
        except AlreadyCompleted:
            pass
        except CannotComplete:
            pass
        else:
            candidate = self._round.result()
            await self._raise_done_round(candidate)
            if candidate.data:
                self._candidate = candidate

    async def _raise_broadcast_data(self, data):
        self._event_system.simulator.raise_event(
            BroadcastDataEvent(
                data=data
            )
        )
        self._event_system.simulator.raise_event(
            ReceivedDataEvent(
                data=data
            )
        )

    async def _raise_broadcast_vote(self, vote: Vote):
        self._event_system.simulator.raise_event(
            BroadcastVoteEvent(
                vote=vote)
        )
        self._event_system.simulator.raise_event(
            ReceivedVoteEvent(
                vote=vote
            )
        )

    async def _raise_done_round(self, candidate: Candidate):
        if candidate.data:
            done_round = DoneRoundEvent(
                is_success=True,
                term_num=self._term.num,
                round_num=self._round.num,
                votes=candidate.votes,
                candidate_data=candidate.data,
                commit_id=candidate.data.prev_id
            )
        else:
            done_round = DoneRoundEvent(
                is_success=False,
                term_num=self._term.num,
                round_num=self._round.num,
                votes=candidate.votes,
                candidate_data=None,
                commit_id=None
            )
        self._event_system.simulator.raise_event(done_round)

    async def _start_new_round(self, term_num: int, round_num: int, voters: Sequence[bytes]):
        if not self._term or self._term.num != term_num:
            self._term = self._term_factory.create_term(
                term_num=term_num,
                voters=voters
            )

        self._round = Round(
            num=round_num,
            term=self._term
        )
        await self._create_data_if_proposer()

    async def _create_data_if_proposer(self):
        try:
            self._term.verify_proposer(self._node_id, self._round.num)
        except InvalidProposer:
            pass
        else:
            new_data = await self._data_factory.create_data(
                data_number=self._candidate.data.number + 1,
                prev_id=self._candidate.data.id,
                term_num=self._term.num,
                round_num=self._round.num,
                prev_votes=self._candidate.votes
            )
            await self._raise_broadcast_data(new_data)

    async def _verify_and_broadcast_vote(self, data):
        if not data.is_not() and self._verify_is_connect_to_candidate(data) and await self._verify_data(data):
            vote = await self._vote_factory.create_vote(data_id=data.id,
                                                        commit_id=self._candidate.data.id,
                                                        term_num=self._round.term.num,
                                                        round_num=self._round.num)
        else:
            vote = await self._vote_factory.create_none_vote(term_num=self._round.term.num,
                                                             round_num=self._round.num)
        await self._raise_broadcast_vote(vote)

    def _verify_is_connect_to_candidate(self, data: Data) -> bool:
        return self._candidate.data.id == data.prev_id

    async def _verify_data(self, data):
        if data.proposer_id == self._node_id:
            return True
        try:
            await self._data_verifier.verify(data)
        except Exception as e:
            return False
        else:
            return True

    def _is_genesis_or_is_connected_genesis(self, data: Data) -> bool:
        return data.number == 0 or data.number == 1

    def _is_next_round(self, term_num: int, round_num: int) -> bool:
        if term_num == self._term.num and round_num == self._round.num + 1:
            return True
        if term_num == self._term.num + 1 and round_num == 0:
            return True
        return False
