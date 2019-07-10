from lft.consensus.layers.sync.sync_round import SyncRound
from lft.consensus.events import BroadcastConsensusDataEvent, BroadcastConsensusVoteEvent, QuorumEvent


class SyncLayer:
    def __init__(self, event_system, data_factory, vote_factory):
        self._event_system = event_system
        self._data_factory = data_factory
        self._vote_factory = vote_factory

        self._sync_round: SyncRound = None

    def _on_sequence_propose(self, sequence):
        self._new_round(sequence.term_num, sequence.round_num, sequence.data)
        self._raise_event_vote()

    def _on_sequence_vote(self, sequence):
        if self._sync_round.expired:
            return

        # 투표를 아예 하지 녀석들에 대한 vote도 만들어서 보내준다. 역시 async layer 에서 보내준다.
        self._sync_round.votes.add_vote(sequence.vote)

        result = self._sync_round.votes.get_result()
        if result is None:
            return

        if result is True:
            self._raise_event_quorum()
        elif result is False:
            # if I am a leader
            self._raise_event_propose()
        self._sync_round.expired = True

    def _new_round(self, term: int, round_: int, data):
        self._sync_round = SyncRound(term, round_, data, self._vote_factory.create_votes())

    def _raise_event_vote(self):
        verifier = self._data_factory.create_verifier()
        try:
            verifier.verify(self._sync_round.data)
        except:
            vote_event = VoteEvent(None, self._sync_round.term_num, self._sync_round.round_num)
        else:
            vote_event = VoteEvent(self._sync_round.data.id, self._sync_round.term_num, self._sync_round.round_num)
        finally:
            self._event_system.raise_event(vote_event)

    def _raise_event_quorum(self):
        precommit_event = QuorumEvent(self._sync_round.votes.get_result(), self._sync_round.data)
        self._event_system.raise_event(precommit_event)

    def _raise_event_propose(self):
        new_data = self._data_factory.create(self._sync_round.term_num, self._sync_round.round_num + 1)
        propose_event = BroadcastConsensusDataEvent(new_data)
        self._event_system.raise_event(propose_event)

