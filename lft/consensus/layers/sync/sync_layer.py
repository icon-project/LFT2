from typing import Sequence

from lft.consensus.data import Data, DataVerifier, DataFactory
from lft.consensus.vote import Vote, VoteVerifier, VoteFactory, Votes
from lft.consensus.layers.sync.candidate_info import CandidateInfo
from lft.consensus.layers.sync.sync_round import SyncRound, RoundResult
from lft.consensus.events import (BroadcastDataEvent, BroadcastVoteEvent,
                                  InitializeEvent, ProposeSequence, VoteSequence,
                                  StartRoundEvent, DoneRoundEvent)
from lft.consensus.layers.sync.temporal_consensus_data_container import TemporalDataContainer
from lft.consensus.term import Term, TermFactory, InvalidProposer
from lft.event import EventSystem, EventRegister


class SyncLayer(EventRegister):
    def __init__(self, node_id: bytes, event_system: EventSystem, data_factory: DataFactory,
                 vote_factory: VoteFactory, term_factory: TermFactory):
        super().__init__(event_system.simulator)
        self._event_system: EventSystem = event_system
        self._data_factory: DataFactory = data_factory
        self._vote_factory: VoteFactory = vote_factory
        self._term_factory: TermFactory = term_factory

        self._data_verifier: DataVerifier = None
        self._vote_verifier: VoteVerifier = None

        self._candidate_info: CandidateInfo = None
        self._temporal_data_container: TemporalDataContainer = None
        self._sync_round: SyncRound = None
        self._term: Term = None
        self._node_id: bytes = node_id

    async def _on_event_initialize(self, init_event: InitializeEvent):
        self._temporal_data_container = TemporalDataContainer(init_event.candidate_data.number)
        self._data_verifier = await self._data_factory.create_data_verifier()
        self._vote_verifier = await self._vote_factory.create_vote_verifier()

        self._candidate_info = CandidateInfo(
            candidate_data=init_event.candidate_data,
            votes=init_event.votes
        )
        self._temporal_data_container.add_data(init_event.candidate_data)

        await self._start_new_round(
            term_num=init_event.term_num,
            round_num=init_event.round_num,
            voters=init_event.voters
        )

    async def _on_event_start_round(self, start_round_event: StartRoundEvent):
        if not self._is_next_round(start_round_event):
            return

        await self._start_new_round(
            term_num=start_round_event.term_num,
            round_num=start_round_event.round_num,
            voters=start_round_event.voters
        )

    async def _on_sequence_propose(self, propose_sequence: ProposeSequence):
        """ Receive propose

        :param propose_sequence:
        :return:
        """
        data = propose_sequence.data
        self._temporal_data_container.add_data(data)
        await self._update_candidate_by_data_if_reach_requirements(data)
        self._sync_round.add_data(data)

        if not self._sync_round.is_voted:
            await self._verify_and_broadcast_vote(data)

        await self._update_round_if_complete()

    async def _on_sequence_vote(self, vote_sequence: VoteSequence):
        self._sync_round.add_vote(vote_sequence.vote)
        await self._update_round_if_complete()

    async def _update_round_if_complete(self):
        if not self._sync_round.is_apply:
            round_result = self._sync_round.get_result()
            if round_result:
                self._sync_round.apply()
                await self._raise_done_round(round_result)
                if round_result.is_success:
                    self._candidate_info = CandidateInfo(
                        candidate_data=round_result.candidate_data,
                        votes=round_result.votes
                    )
                    self._temporal_data_container.update_criteria(self._candidate_info.candidate_data.number)

    async def _raise_broadcast_data(self, data):
        self._event_system.simulator.raise_event(
            BroadcastDataEvent(
                data=data
            )
        )

    async def _raise_broadcast_vote(self, vote: Vote):
        self._event_system.simulator.raise_event(
            BroadcastVoteEvent(
                vote=vote)
        )

    async def _raise_done_round(self, round_result: RoundResult):
        if round_result.is_success:
            done_round = DoneRoundEvent(
                is_success=True,
                term_num=round_result.term_num,
                round_num=round_result.round_num,
                votes=round_result.votes,
                candidate_data=round_result.candidate_data,
                commit_id=round_result.candidate_data.prev_id
            )
        else:
            done_round = DoneRoundEvent(
                is_success=False,
                term_num=round_result.term_num,
                round_num=round_result.round_num,
                votes=round_result.votes,
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

        self._sync_round = SyncRound(
            term=self._term,
            round_num=round_num
        )
        await self._create_data_if_proposer()

    async def _create_data_if_proposer(self):
        try:
            self._term.verify_proposer(self._node_id, self._sync_round.round_num)
        except InvalidProposer:
            pass
        else:
            new_data = await self._data_factory.create_data(
                data_number=self._candidate_info.candidate_data.number + 1,
                prev_id=self._candidate_info.candidate_data.id,
                term_num=self._sync_round.term_num,
                round_num=self._sync_round.round_num,
                prev_votes=self._candidate_info.votes
            )
            await self._raise_broadcast_data(new_data)

    async def _update_candidate_by_data_if_reach_requirements(self, data):
        if data.is_not():
            return

        if self._is_genesis_or_is_connected_genesis(data):
            return

        prev_votes = Votes.deserialize(data.prev_votes)
        if prev_votes.data_id != self._candidate_info.candidate_data.id:
            if prev_votes.term_num == self._candidate_info.candidate_data.term_num:
                if prev_votes.round_num > self._candidate_info.candidate_data.round_num:
                    self._candidate_info = CandidateInfo(
                        candidate_data=self._temporal_data_container.get_data(data.number - 1, prev_votes.data_id),
                        votes=prev_votes.votes
                    )
            elif prev_votes.term_num > self._candidate_info.candidate_data.term_num:
                self._candidate_info = CandidateInfo(
                    candidate_data=self._temporal_data_container.get_data(data.number - 1, prev_votes.data_id),
                    votes=prev_votes.votes
                )

    def _is_genesis_or_is_connected_genesis(self, data: Data) -> bool:
        return data.number == 0 or data.number == 1

    async def _verify_and_broadcast_vote(self, data):
        if self._node_id == data.proposer_id:
            vote = await self._vote_factory.create_vote(data_id=data.id,
                                                        commit_id=self._candidate_info.candidate_data.id,
                                                        term_num=self._sync_round.term_num,
                                                        round_num=self._sync_round.round_num)
        elif self._verify_is_connect_to_candidate(data) and await self._verify_data(data) and not data.is_not():
            vote = await self._vote_factory.create_vote(data_id=data.id,
                                                        commit_id=self._candidate_info.candidate_data.id,
                                                        term_num=self._sync_round.term_num,
                                                        round_num=self._sync_round.round_num)
        else:
            vote = await self._vote_factory.create_none_vote(term_num=self._sync_round.term_num,
                                                             round_num=self._sync_round.round_num)
        await self._raise_broadcast_vote(vote)
        self._sync_round.is_voted = True

    def _verify_is_connect_to_candidate(self, data: Data) -> bool:
        return self._candidate_info.candidate_data.id == data.prev_id

    async def _verify_data(self, data):
        if data.proposer_id == self._node_id:
            return True
        try:
            await self._data_verifier.verify(data)
        except Exception as e:
            return False
        else:
            return True

    def _is_next_round(self, start_round_event: StartRoundEvent) -> bool:
        if start_round_event.term_num == self._sync_round.term_num \
                and start_round_event.round_num == self._sync_round.round_num + 1:
            return True
        elif start_round_event.term_num == self._sync_round.term_num + 1 \
                and start_round_event.round_num == 0:
            return True
        return False

    _handler_prototypes = {
        InitializeEvent: _on_event_initialize,
        StartRoundEvent: _on_event_start_round,
        ProposeSequence: _on_sequence_propose,
        VoteSequence: _on_sequence_vote
    }
