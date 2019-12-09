import pytest

from lft.app.data import DefaultData
from lft.app.vote import DefaultVote
from lft.consensus.events import BroadcastVoteEvent, ReceiveVoteEvent
from tests.election.setup_election import setup_election, CANDIDATE_ID, LEADER_ID

PROPOSE_ID = b"b"


@pytest.mark.asyncio
@pytest.mark.parametrize("propose_id,propose_prev_id,expected_vote_data_id",
                         [(b"b", CANDIDATE_ID, b"b"),
                          (b"b", b"other_id", DefaultVote.NoneVote),
                          (LEADER_ID, None, DefaultVote.NoneVote)])
async def test_receive_data(propose_id, propose_prev_id, expected_vote_data_id):
    # TODO propose not data, correct data, non_connection_data
    """ GIVEN Election with candidate_data and ProposeSequence, setup
    WHEN raise ProposeSequence
    THEN Receive VoteEvent about ProposeSequence
    """
    # GIVEN
    event_system, election, voters = await setup_election(peer_num=7)
    await election.round_start()

    propose = DefaultData(id_=PROPOSE_ID,
                          prev_id=propose_prev_id,
                          proposer_id=LEADER_ID,
                          number=1,
                          epoch_num=0,
                          round_num=0,
                          prev_votes=[])
    # WHEN
    await election.receive_data(propose)
    # THEN
    assert len(event_system.simulator.raise_event.call_args_list) == 2

    event = event_system.simulator.raise_event.call_args_list[0][0][0]
    assert isinstance(event, BroadcastVoteEvent)
    assert event.vote.data_id == expected_vote_data_id

    event = event_system.simulator.raise_event.call_args_list[1][0][0]
    assert isinstance(event, ReceiveVoteEvent)
    assert event.vote.data_id == expected_vote_data_id

    event_system.simulator.raise_event.reset_mock()

    # Test double propose
    # GIVEN
    second_propose = DefaultData(id_=PROPOSE_ID,
                                 prev_id=propose_prev_id,
                                 proposer_id=LEADER_ID,
                                 number=1,
                                 epoch_num=0,
                                 round_num=0,
                                 prev_votes=[])

    # WHEN
    await election.receive_data(data=second_propose)
    # THEN
    event_system.simulator.raise_event.assert_not_called()
