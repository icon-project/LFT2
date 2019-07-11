from typing import TYPE_CHECKING, DefaultDict, List
from collections import defaultdict
from lft.consensus.events import ProposeEvent, VoteEvent, ProposeSequence, VoteSequence
from lft.consensus.factories import ConsensusData, ConsensusVote


if TYPE_CHECKING:
    from lft.event import EventSimulator


DataCollection = dict
VoteCollection = defaultdict(list)


class Sequencer:
    def __init__(self, event_system: 'EventSimulator'):
        self._event_system = event_system
        self._event_system.register_handler(ProposeEvent, self._on_event_propose)

        self._data: DefaultDict[int, DefaultDict[bytes, ConsensusData]] = defaultdict(DataCollection)
        self._votes: DefaultDict[int, DefaultDict[int, List[ConsensusVote]]] = defaultdict(VoteCollection)

    async def _on_event_propose(self, event: ProposeEvent):
        # data verification

        self._data[event.era][event.round] = event.data

        new_event = ProposeSequence(event.data, event.era, event.round, event.leader)
        self._event_system.raise_event(new_event)

        for vote in self._votes[event.era][event.round]:
            new_event = VoteSequence(vote)
            self._event_system.raise_event(new_event)

        del self._votes[event.era][event.round]
        if not self._votes[event.era]:
            del self._votes[event.era]

    async def _on_event_vote(self, event: VoteEvent):
        # vote verification
        # check event.era and event.round have already finished.

        self._vote_events[event.vote.term_num][event.vote.round].append(event)

