import pytest

from lft.app.data import DefaultData
from lft.app.vote import DefaultVoteFactory
from lft.consensus.events import RoundEndEvent
from tests.election.setup_election import setup_election, CANDIDATE_ID, LEADER_ID

PEER_NUM = 7
PROPOSE_ID = b'propose'


@pytest.mark.asyncio
@pytest.mark.parametrize("success_vote_num, none_vote_num, lazy_vote_num, expected_success, expected_determinative",
                         [(5, 2, 0, True, True),
                          (5, 0, 0, True, True),
                          (2, 5, 0, False, True),
                          (0, 5, 0, False, True),
                          (3, 4, 0, False, True),
                          (4, 0, 0, False, False),
                          (4, 1, 7, False, True)]
                         )
async def test_receive_vote(success_vote_num, none_vote_num, lazy_vote_num, expected_success, expected_determinative):
    """ GIVEN election and propose data,
    WHEN repeats _on_add_votes amount of vote_num
    THEN raised expected RoundEndEvent
    """

    # GIVEN
    election, consensus_data, event_system, voters = await set_election_for_receive_vote()

    # WHEN

    await do_votes(election, success_vote_num, none_vote_num, lazy_vote_num, voters)

    # THEN
    if expected_determinative:
        event_system.simulator.raise_event.assert_called_once()
        event = event_system.simulator.raise_event.call_args_list[0][0][0]
        assert isinstance(event, RoundEndEvent)
        if expected_success:
            verify_success_round_end(round_end=event,
                                     expected_candidate_id=consensus_data.id,
                                     expected_commit_id=CANDIDATE_ID)

        else:
            verify_fail_round_end(round_end=event)


async def do_votes(election, success_vote_num, none_vote_num, lazy_vote_num, voters):
    validator_vote_factories = [DefaultVoteFactory(x) for x in voters]

    for i in range(success_vote_num):
        await do_vote(
            election,
            await validator_vote_factories[i].create_vote(
                data_id=PROPOSE_ID,
                commit_id=CANDIDATE_ID,
                epoch_num=0,
                round_num=1
            )
        )
    for i in range(none_vote_num):
        await do_vote(
            election,
            validator_vote_factories[success_vote_num + i].create_none_vote(
                epoch_num=0,
                round_num=1
            )
        )
    for i in range(lazy_vote_num):
        await do_vote(
            election,
            validator_vote_factories[i].create_lazy_vote(
                voter_id=voters[i],
                epoch_num=0,
                round_num=1
            )
        )


async def set_election_for_receive_vote():
    event_system, election, voters = await setup_election(PEER_NUM)
    await election.round_start()
    consensus_data = DefaultData(
        id_=PROPOSE_ID,
        prev_id=CANDIDATE_ID,
        proposer_id=LEADER_ID,
        number=1,
        epoch_num=0,
        round_num=1,
        prev_votes=[]
    )
    await election.receive_data(data=consensus_data)
    event_system.simulator.raise_event.reset_mock()
    return election, consensus_data, event_system, voters


@pytest.mark.asyncio
@pytest.mark.parametrize("is_success", [True, False])
async def test_not_deterministic_to_deterministic(is_success):
    # GIVEN
    election, consensus_data, event_system, voters = await set_election_for_receive_vote()

    await do_votes(election, 3, 2, 7, voters)

    event_system.simulator.raise_event.assert_called_once()
    event_system.simulator.raise_event.reset_mock()
    assert election._messages.result.is_lazy()

    # WHEN
    if is_success:
        await do_votes(election, 2, 0, 0, voters[5:7])
    else:
        await do_votes(election, 0, 2, 0, voters[5:7])
    # THEN
    if is_success:
        assert election.result_id == consensus_data.id
    else:
        assert not election.result_id
        assert election._messages.result.is_none()


async def do_vote(election, vote):
    await election.receive_vote(vote)


def verify_fail_round_end(round_end: RoundEndEvent):
    verify_round_num_is_correct(round_end)
    assert not round_end.candidate_id
    assert not round_end.commit_id


def verify_success_round_end(round_end: RoundEndEvent,
                             expected_candidate_id: bytes,
                             expected_commit_id: bytes):
    assert round_end.candidate_id
    verify_round_num_is_correct(round_end)
    assert round_end.candidate_id == expected_candidate_id
    assert round_end.commit_id == expected_commit_id


def verify_round_num_is_correct(round_end):
    assert round_end.round_num == 1
    assert round_end.epoch_num == 0
