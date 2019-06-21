import asyncio
from typing import TYPE_CHECKING, Any
from lft.state import State
from lft.consensus.events import ProposeResultEvent, VoteEvent, VoteResultEvent, CommitResultEvent

if TYPE_CHECKING:
    from lft.consensus import Consensus
    from lft.consensus.events import RoundEvent


class ConsensusState(State):
    def __init__(self, consensus: 'Consensus'):
        self._consensus = consensus


class ProposeState(ConsensusState):
    async def on_enter(self, event: 'RoundEvent'):
        if event.leader_id == self._consensus.leader_id:
            data = self._consensus.data_factory.create_data()
            propose_event = ProposeResultEvent(data)

            self._consensus.event_system.raise_event(propose_event)
        else:
            async def _complain():
                await asyncio.sleep(2)
                self._consensus.event_system.raise_event(new_event)
            asyncio.ensure_future(_complain())

    async def on_exit(self, event: Any):
        pass


class VoteState(ConsensusState):
    _votes = None
    _handler = None

    async def on_enter(self, event: Any):
        self._votes = self._consensus.vote_factory.create_votes()
        self._handler = self._consensus.event_system.register_handler(VoteEvent, self.on_event_vote)

        vote = self._consensus.vote_factory.create_vote()
        vote_event = VoteEvent(vote)
        self._consensus.event_system.raise_event(vote_event)

    async def on_exit(self, event: Any):
        self._consensus.event_system.unregister_handler(VoteEvent, self._handler)

        self._votes = None
        self._handler = None

    async def on_event_vote(self, event: VoteEvent):
        self._votes.add_vote(event.vote)
        if self._votes.get_result() is not None:
            event = VoteResultEvent(self._votes)
            self._consensus.event_system.raise_event(event)

    def __del__(self):
        if self._handler:
            self._consensus.event_system.unregister_handler(VoteEvent, self._handler)
            self._handler = None

# Vote 를 전연적으로 저장 해야할 수도 있음


class CommitState(ConsensusState):
    async def on_enter(self, event: Any):
        commit_event = CommitResultEvent(self._consensus.locked_data)
        self._consensus.event_system.raise_event(commit_event)

    async def on_exit(self, event: Any):
        pass
