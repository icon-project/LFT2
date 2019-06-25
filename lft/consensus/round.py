import asyncio
from typing import TYPE_CHECKING, Any
from lft.state import StateMachine, State
from lft.consensus.events import ProposeResultEvent, VoteResultEvent, CommitResultEvent

if TYPE_CHECKING:
    from lft.consensus.events import RoundEvent


class Round(StateMachine):
    def __init__(self, era: int, round_: int, leader: bytes):
        super().__init__()

        self.era = era
        self.round = round_

        self.add_state("propose", ProposeState(self))
        self.add_state("vote", VoteState(self))
        self.add_state("commit", CommitState(self))
        self.add_transition("propose", "vote", ProposeResultEvent)
        self.add_transition("vote", "propose", VoteResultEvent, lambda e: e.votes.get_result() is False)
        self.add_transition("vote", "commit", VoteResultEvent, lambda e: e.votes.get_result() is True)
        self.add_transition("commit", "propose", CommitResultEvent)


class RoundState(State):
    def __init__(self, round_: 'Round'):
        self._round = round_


class ProposeState(RoundState):
    async def on_enter(self, event: 'RoundEvent'):
        if event.leader_id == self._round.leader_id:
            data = self._round.data_factory.create_data()
            propose_event = ProposeResultEvent(data)

            self._round.event_system.raise_event(propose_event)
        else:
            async def _complain():
                await asyncio.sleep(2)
                self._round.event_system.raise_event(new_event)
            asyncio.ensure_future(_complain())

    async def on_exit(self, event: Any):
        pass


class VoteState(RoundState):
    _votes = None
    _handler = None

    async def on_enter(self, event: Any):
        self._votes = self._round.vote_factory.create_votes()
        self._handler = self._round.event_system.register_handler(VoteEvent, self.on_event_vote)

        vote = self._round.vote_factory.create_vote()
        vote_event = VoteEvent(vote)
        self._round.event_system.raise_event(vote_event)

    async def on_exit(self, event: Any):
        self._round.event_system.unregister_handler(VoteEvent, self._handler)

        self._votes = None
        self._handler = None

    async def on_event_vote(self, event: VoteEvent):
        self._votes.add_vote(event.vote)
        if self._votes.get_result() is not None:
            event = VoteResultEvent(self._votes)
            self._round.event_system.raise_event(event)

    def __del__(self):
        if self._handler:
            self._round.event_system.unregister_handler(VoteEvent, self._handler)
            self._handler = None

# Vote 를 전연적으로 저장 해야할 수도 있음


class CommitState(RoundState):
    async def on_enter(self, event: Any):
        commit_event = CommitResultEvent(self._round.locked_data)
        self._round.event_system.raise_event(commit_event)

    async def on_exit(self, event: Any):
        pass
