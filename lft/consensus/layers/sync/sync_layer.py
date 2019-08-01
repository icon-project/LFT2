from lft.consensus.factories import ConsensusData, ConsensusDataFactory, ConsensusVoteFactory, ConsensusVote, \
    ConsensusDataVerifier, ConsensusVoteVerifier
from lft.consensus.layers.sync.sync_round import SyncRound
from lft.consensus.events import BroadcastConsensusDataEvent, BroadcastConsensusVoteEvent, DoneRoundEvent,\
    InitializeEvent, ProposeSequence, VoteSequence
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

        self._candidate_data: ConsensusData = None
        self._sync_round: SyncRound = None
        self._term: Term = None
        self._register_handler()

    def _register_handler(self):
        self._event_system.simulator.register_handler(InitializeEvent, self._on_init)
        self._event_system.simulator.register_handler(ProposeSequence, self._on_sequence_propose)
        self._event_system.simulator.register_handler(VoteSequence, self._on_sequence_vote)

    async def _on_init(self, init_event: InitializeEvent):
        print("start init event")
        self._candidate_data = init_event.candidate_data
        self._term = self._term_factory.create_term(term_num=init_event.term_num,
                                                    voters=init_event.voters)

        self._sync_round = SyncRound(term=self._term,
                                     round_num=init_event.round_num,
                                     datas=None,
                                     votes=None
                                     )

        self._data_verifier = await self._data_factory.create_data_verifier()
        self._vote_verifier = await self._vote_factory.create_vote_verifier()

    async def _on_sequence_propose(self, propose_event: ProposeSequence):
        """ Receive propose

        :param propose_event:
        :return:
        """
        data = propose_event.data
        vote = None
        if self._verify_is_connect_to_candidate(data) and await self._verify_data(data):
            # TODO Broadcast Correct Vote
            vote = await self._vote_factory.create_vote(data_id=data.id,
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

    def _verify_is_connect_to_candidate(self, data: ConsensusData) -> bool:
        print(f"candidate id : {self._candidate_data.id} data prev_id : {data.prev_id} ")
        if self._candidate_data.id == data.prev_id:
            return True
        return False

    async def _verify_data(self, data):
        try:
            await self._data_verifier.verify(data)
        except Exception as e:
            print(f"verify Exception : {e}")
            return False
        else:
            return True

    def _raise_event_quorum(self):
        precommit_event = DoneRoundEvent(self._sync_round.votes.get_result(), self._sync_round.data)
        self._event_system.raise_event(precommit_event)

    async def _on_sequence_vote(self, vote_event: VoteSequence):
        # if self._sync_round.expired:
        #     return
        #
        # # 투표를 아예 하지 녀석들에 대한 vote도 만들어서 보내준다. 역시 async layer 에서 보내준다.
        # self._sync_round.votes.add_vote(sequence.vote)
        #
        # result = self._sync_round.votes.get_result()
        # if result is None:
        #     return
        #
        # if result is True:
        #     self._raise_event_quorum()
        # elif result is False:
        #     # if I am a leader
        #     self._raise_event_propose()
        # self._sync_round.expired = True
        pass

    def _new_round(self, term: int, round_: int, data):
        self._sync_round = SyncRound(term, round_, data, self._vote_factory.create_votes())

    # def _raise_event_vote(self):
    #     verifier = self._data_factory.create_verifier()
    #     try:
    #         verifier.verify(self._sync_round.data)
    #     except:
    #         vote_event = VoteEvent(None, self._sync_round.term_num, self._sync_round.round_num)
    #     else:
    #         vote_event = VoteEvent(self._sync_round.data.id, self._sync_round.term_num, self._sync_round.round_num)
    #     finally:
    #         self._event_system.raise_event(vote_event)
    #
    # def _raise_event_quorum(self):
    #     precommit_event = QuorumEvent(self._sync_round.votes.get_result(), self._sync_round.data)
    #     self._event_system.raise_event(precommit_event)
    #
    # def _raise_event_propose(self):
    #     new_data = self._data_factory.create(self._sync_round.term_num, self._sync_round.round_num + 1)
    #     propose_event = BroadcastConsensusDataEvent(new_data)
    #     self._event_system.raise_event(propose_event)
