from mock import MagicMock
from typing import Tuple, List
from lft.app.data import DefaultDataFactory, DefaultData
from lft.app.vote import DefaultVoteFactory
from lft.app.epoch import RotateEpoch
from lft.consensus.messages.data import DataPool
from lft.consensus.messages.vote import VotePool
from lft.consensus.election import Election
from lft.event import EventSystem

CANDIDATE_ID = b'a'
TEST_NODE_ID = bytes([2])
LEADER_ID = bytes([1])


async def setup_election(peer_num: int) -> Tuple[EventSystem, Election, List[bytes]]:
    event_system = MagicMock(EventSystem())
    voters = [bytes([x]) for x in range(peer_num)]
    data_factory = DefaultDataFactory(TEST_NODE_ID)
    vote_factory = DefaultVoteFactory(TEST_NODE_ID)
    data_pool = DataPool()
    vote_pool = VotePool()

    genesis_data = DefaultData(
        id_=CANDIDATE_ID,
        prev_id=b'',
        proposer_id=TEST_NODE_ID,
        number=0,
        epoch_num=0,
        round_num=0,
        prev_votes=()
    )
    data_pool.add_data(genesis_data)

    election = Election(TEST_NODE_ID, RotateEpoch(0, voters), genesis_data.round_num + 1,
                        event_system, data_factory, vote_factory, data_pool, vote_pool)
    election._candidate_id = CANDIDATE_ID
    return event_system, election, voters
