from lft.consensus.data import ConsensusDataFactory, ConsensusVoteFactory, ConsensusDataVerifier, ConsensusVoteVerifier, \
    ConsensusData, ConsensusVote
from lft.consensus.layers.sync.candidate_info import CandidateInfo
from lft.consensus.layers.sync.sync_round import SyncRound, RoundResult
from lft.consensus.events import BroadcastConsensusDataEvent, BroadcastConsensusVoteEvent, DoneRoundEvent, \
    InitializeEvent, ProposeSequence, VoteSequence, ReceivedConsensusVoteEvent, ReceivedConsensusDataEvent, \
    StartRoundEvent
from lft.consensus.term import Term
from lft.consensus.term.factories import TermFactory
from lft.event import EventSystem


class SyncLayer:
    def __init__(self, event_system: EventSystem, data_factory: ConsensusDataFactory,
                 vote_factory: ConsensusVoteFactory, term_factory: TermFactory):
        self._event_system: EventSystem = event_system
        self._data_factory: ConsensusDataFactory = data_factory
        self._vote_factory: ConsensusVoteFactory = vote_factory
        self._term_factory: TermFactory = term_factory

        self._data_verifier: ConsensusDataVerifier = None
        self._vote_verifier: ConsensusVoteVerifier = None

        self._candidate_info: CandidateInfo = None
        self._sync_round: SyncRound = None
        self._term: Term = None
        self._node_id: bytes = None
        self._register_handler()

    def _register_handler(self):
        self._event_system.simulator.register_handler(InitializeEvent, self._on_init)
        self._event_system.simulator.register_handler(ProposeSequence, self._on_sequence_propose)
        self._event_system.simulator.register_handler(VoteSequence, self._on_sequence_vote)
        self._event_system.simulator.register_handler(StartRoundEvent, self._on_start_round)

    async def _on_init(self, init_event: InitializeEvent):
        self._candidate_info = CandidateInfo(
            candidate_data=init_event.candidate_data,
            votes=init_event.votes
        )
        self._node_id = init_event.node_id
        self._term = self._term_factory.create_term(term_num=init_event.term_num,
                                                    voters=init_event.voters)

        self._sync_round = SyncRound(term=self._term,
                                     round_num=init_event.round_num
                                     )
        self._data_verifier = await self._data_factory.create_data_verifier()
        self._vote_verifier = await self._vote_factory.create_vote_verifier()

    async def _on_sequence_propose(self, propose_sequence: ProposeSequence):
        """ Receive propose

        :param propose_sequence:
        :return:
        """
        data = propose_sequence.data
        vote = None
        if self._verify_is_connect_to_candidate(data) and await self._verify_data(data) and not data.is_not():
            vote = await self._vote_factory.create_vote(data_id=data.id,
                                                        commit_id=self._candidate_info.candidate_data.id,
                                                        term_num=self._sync_round.term_num,
                                                        round_num=self._sync_round.round_num)
        else:
            vote = await self._vote_factory.create_none_vote(term_num=self._sync_round.term_num,
                                                             round_num=self._sync_round.round_num)

        self._sync_round.add_data(data)
        if not self._sync_round.is_voted:
            self._sync_round.is_voted = True
            self._raise_broadcast_vote(vote)

    def _raise_broadcast_vote(self, vote: ConsensusVote):
        self._event_system.simulator.raise_event(BroadcastConsensusVoteEvent(vote=vote))

        receive_vote_event = ReceivedConsensusVoteEvent(vote=vote)
        receive_vote_event.deterministic = True
        self._event_system.simulator.raise_event(receive_vote_event)

    def _verify_is_connect_to_candidate(self, data: ConsensusData) -> bool:
        if self._candidate_info.candidate_data.id == data.prev_id:
            return True
        return False

    async def _verify_data(self, data):
        try:
            await self._data_verifier.verify(data)
        except Exception as e:
            return False
        else:
            return True

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

    async def _start_new_round(self):
        self._sync_round = SyncRound(
            term=self._term,
            round_num=self._sync_round.round_num + 1
        )
        if self._term.get_proposer_id(self._sync_round.round_num) == self._node_id:
            self._event_system.simulator.raise_event(BroadcastConsensusDataEvent(
                data=proposer
            ))

            received_event = ReceivedConsensusDataEvent(
                data=proposer
            )
            received_event.deterministic = True
            self._event_system.simulator.raise_event(received_event)

    async def _raise_done_round(self, round_result: RoundResult):
        if round_result.is_success:
            done_round = DoneRoundEvent(
                is_success=True,
                term_num=round_result.term_num,
                round_num=round_result.round_num,
                votes=round_result.votes,
                candidate_data=round_result.candidate_data,
                commit_data=self._candidate_info.candidate_data
           )
        else:
            done_round = DoneRoundEvent(
                is_success=False,
                term_num=round_result.term_num,
                round_num=round_result.round_num,
                votes=round_result.votes,
                candidate_data=None,
                commit_data=None
            )
        self._event_system.simulator.raise_event(done_round)

    async def _on_start_round(self, start_round_event: StartRoundEvent):
        if self._term.num != start_round_event.term_num:
            self._term = self._term_factory.create_term(start_round_event.term_num, start_round_event.voters)
        self._sync_round = SyncRound(
            term=self._term,
            round_num=start_round_event.round_num
        )
        print("on_start_round")
        print(self._node_id)
        print(self._sync_round.round_num)
        print(self._term.get_proposer_id(self._sync_round.round_num))
        try:
            self._term.verify_proposer(self._node_id, self._sync_round.round_num)
        except Exception:
            pass
        else:
            print("is leader")
            new_data = await self._data_factory.create_data(
                data_number=self._candidate_info.candidate_data.number + 1,
                prev_id=self._candidate_info.candidate_data.id,
                term_num=self._sync_round.term_num,
                round_num=self._sync_round.round_num,
                prev_votes=self._candidate_info.votes
            )
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
            vote = await self._vote_factory.create_vote(
                data_id=new_data.id,
                commit_id=self._candidate_info.candidate_data.id,
                term_num=self._term.num,
                round_num=self._sync_round.round_num
            )
            self._event_system.simulator.raise_event(
                BroadcastConsensusVoteEvent(
                    vote=vote
                )
            )
            self._event_system.simulator.raise_event(
                ReceivedConsensusVoteEvent(
                    vote=vote
                )
            )


