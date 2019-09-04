from typing import Sequence

from lft.app.data.consensus_votes import ConsensusVotes
from lft.consensus.data import ConsensusDataFactory, ConsensusVoteFactory, ConsensusDataVerifier, ConsensusVoteVerifier, \
    ConsensusData, ConsensusVote
from lft.consensus.layers.sync.candidate_info import CandidateInfo
from lft.consensus.layers.sync.sync_round import SyncRound, RoundResult
from lft.consensus.events import BroadcastConsensusDataEvent, BroadcastConsensusVoteEvent, DoneRoundEvent, \
    InitializeEvent, ProposeSequence, VoteSequence, ReceivedConsensusVoteEvent, ReceivedConsensusDataEvent, \
    StartRoundEvent
from lft.consensus.layers.sync.temporal_consensus_data_container import TemporalConsensusDataContainer
from lft.consensus.term import Term
from lft.consensus.term.factories import TermFactory
from lft.consensus.term.term import InvalidProposer
from lft.event import EventSystem
from lft.event.event_handler_manager import EventHandlerManager


class SyncLayer(EventHandlerManager):
    def __init__(self, node_id: bytes, event_system: EventSystem, data_factory: ConsensusDataFactory,
                 vote_factory: ConsensusVoteFactory, term_factory: TermFactory):
        super().__init__(event_system)
        self._event_system: EventSystem = event_system
        self._data_factory: ConsensusDataFactory = data_factory
        self._vote_factory: ConsensusVoteFactory = vote_factory
        self._term_factory: TermFactory = term_factory

        self._data_verifier: ConsensusDataVerifier = None
        self._vote_verifier: ConsensusVoteVerifier = None

        self._candidate_info: CandidateInfo = None
        self._temporal_data_container: TemporalConsensusDataContainer = None
        self._sync_round: SyncRound = None
        self._term: Term = None
        self._node_id: bytes = node_id
        self._register_handler()

    def _register_handler(self):
        self._add_handler(InitializeEvent, self._on_event_initialize)
        self._add_handler(StartRoundEvent, self._on_event_start_round)
        self._add_handler(ProposeSequence, self._on_sequence_propose)
        self._add_handler(VoteSequence, self._on_sequence_vote)

    async def _on_event_initialize(self, init_event: InitializeEvent):
        self._temporal_data_container = TemporalConsensusDataContainer(init_event.candidate_data.number)
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
        if data.prev_votes:
            await self._check_and_update_candidate(data)
        self._sync_round.add_data(data)

        if not self._sync_round.is_voted:
            await self._verify_and_broadcast_vote(data)

    async def _on_sequence_vote(self, vote_sequence: VoteSequence):
        self._sync_round.add_vote(vote_sequence.vote)
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

    async def _raise_new_data_events(self, new_data):
        self._event_system.simulator.raise_event(
            BroadcastConsensusDataEvent(
                data=new_data
            )
        )
        self._event_system.simulator.raise_event(
            ReceivedConsensusDataEvent(
                data=new_data
            )
        )

    async def _raise_broadcast_vote(self, vote: ConsensusVote):
        self._event_system.simulator.raise_event(BroadcastConsensusVoteEvent(vote=vote))

        receive_vote_event = ReceivedConsensusVoteEvent(vote=vote)
        receive_vote_event.deterministic = True
        self._event_system.simulator.raise_event(receive_vote_event)

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
            await self._raise_new_data_events(new_data)

    async def _check_and_update_candidate(self, data):
        prev_votes = ConsensusVotes.from_list(data.prev_votes)
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
        # TODO note

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

    def _verify_is_connect_to_candidate(self, data: ConsensusData) -> bool:
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
