from typing import Optional, TYPE_CHECKING
from state import StateMachine
from consensus.states import ProposeState, VoteState, CommitState
from consensus.events import ProposeResultEvent, CommitResultEvent, VoteResultEvent
if TYPE_CHECKING:
    from event import EventSystem
    from consensus.factories import ConsensusDataFactory, ConsensusVoteFactory, ConsensusData


class Consensus:
    def __init__(self, event_system: 'EventSystem', leader_id: bytes,
                 data_factory: 'ConsensusDataFactory', vote_factory: 'ConsensusVoteFactory'):
        self.event_system = event_system
        self.data_factory = data_factory
        self.vote_factory = vote_factory
        self.leader_id = leader_id

        self.round: Optional[int] = 0
        self.voters = []

        self.locked_data: Optional['ConsensusData'] = None
        self.preferred_data: Optional['ConsensusData'] = None

        self._state_machine = StateMachine()
        self._state_machine.add_state("propose", ProposeState(self))
        self._state_machine.add_state("vote", VoteState(self))
        self._state_machine.add_state("commit", CommitState(self))
        self._state_machine.add_transition("propose", "vote", ProposeResultEvent)
        self._state_machine.add_transition("vote", "propose", VoteResultEvent, lambda e: e.votes.get_result() is False)
        self._state_machine.add_transition("vote", "commit", VoteResultEvent, lambda e: e.votes.get_result() is True)
        self._state_machine.add_transition("commit", "propose", CommitResultEvent)

        # 비동기 상황에서의 고려가 필요하다
