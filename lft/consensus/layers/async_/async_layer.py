from collections import defaultdict
from typing import DefaultDict, Dict
from lft.consensus.layers.async_ import AsyncRound


class AsyncLayer:
    def __init__(self, event_system):
        self._event_system = event_system
        self._term: int = None
        self._round: int = None

        # self._async_rounds[term][round] = AsyncRound
        self._async_rounds: DefaultDict[int, Dict[int, AsyncRound]] = defaultdict(dict)

    def _on_event_sync_complete(self, event):
        self._term = event.new_term
        self._round = event.new_round

    def _on_event_propose(self, event):
        # 새로운 term 이 시작 되는 건 어떻게 판단하지?
        if self._term > event.term:
            return
        if self._term == event.term and self._round > event.round:
            return

        async_round = self._new_or_get_round(event.term, event.round)
        if async_round.data:
            return
        async_round.data = event.data

        self._raise_quorum_event(event.data.prev_votes.get_result(), None)
        self._raise_propose_sequence(event.term, event.round, event.data)
        for vote_event in async_round.vote_events:
            self._raise_vote_sequence(vote_event.vote)

    def _on_event_vote(self, event):
        async_round = self._new_or_get_round(event.term, event.round)
        async_round.vote_events.append(event)

        if async_round.data:
            self._raise_vote_sequence(event.vote)

    def _on_event_quorum(self, event):
        self._trim_round(event.term, event.round)

    def _new_or_get_round(self, term: int, round_: int):
        try:
            async_round = self._async_rounds[term][round_]
        except KeyError:
            async_round = AsyncRound(term, round_)
            self._async_rounds[term][round_] = async_round

        return async_round

    def _raise_quorum_event(self, data_id):
        precommit_event = QuorumEvent(data_id, None)
        self._event_system.raise_event(precommit_event)

    def _raise_propose_sequence(self, term: int, round_: int, data):
        propose_sequence = ProposeSequence(event.term, event.round, event.data)
        self._event_system.raise_event(propose_sequence)

    def _raise_vote_sequence(self, vote):
        vote_sequence = VoteSequence(vote)
        self._event_system.raise_event(vote_sequence)

    def _trim_round(self, term: int, round_: int):
        remove_terms = [t for t in self._async_rounds if t < term]
        for remove_term in remove_terms:
            del self._async_rounds[remove_term]

        try:
            rounds = self._async_rounds[term]
        except KeyError:
            pass
        else:
            remove_rounds = [r for r in rounds if r < round_]
            for remove_round in remove_rounds:
                del rounds[remove_round]

