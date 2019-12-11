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
                          (4, 1, 2, False, True)]
                         )
async def test_on_vote_sequence(success_vote_num, none_vote_num, lazy_vote_num, expected_success, expected_determinative):
    """ GIVEN SyncRound and propose data,
    WHEN repeats _on_add_votes amount of vote_num
    THEN raised expected RoundEndEvent
    """

    # GIVEN
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

    # WHEN
    async def do_vote(vote):
        await election.receive_vote(vote)

    validator_vote_factories = [DefaultVoteFactory(x) for x in voters]
    for i in range(success_vote_num):
        await do_vote(
            await validator_vote_factories[i].create_vote(
                data_id=PROPOSE_ID,
                commit_id=CANDIDATE_ID,
                epoch_num=0,
                round_num=1
            )
        )
    for i in range(none_vote_num):
        await do_vote(
            validator_vote_factories[success_vote_num + i].create_none_vote(
                epoch_num=0,
                round_num=1
            )
        )

    for i in range(lazy_vote_num):
        await do_vote(
            validator_vote_factories[success_vote_num + none_vote_num + i].create_lazy_vote(
                voter_id=voters[success_vote_num + none_vote_num + i],
                epoch_num=0,
                round_num=1
            )
        )

    # THEN
    if expected_determinative:
        event_system.simulator.raise_event.called_once()
        event = event_system.simulator.raise_event.call_args_list[0][0][0]
        assert isinstance(event, RoundEndEvent)
        if expected_success:
            verify_success_round_end(round_end=event,
                                     expected_candidate_id=consensus_data.id,
                                     expected_commit_id=CANDIDATE_ID)

        else:
            verify_fail_round_end(round_end=event)


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
