import pytest
import random
from unittest.mock import MagicMock
from lft.app.data import DefaultDataFactory, DefaultData
from lft.app.vote import DefaultVoteFactory, DefaultVote
from lft.app.epoch import RotateEpoch
from lft.consensus import Consensus
from lft.consensus.events import RoundEndEvent
from lft.event import EventSystem


params = dict()
params["normal"] = {}
params["normal"]["epochs"] = [
    RotateEpoch(num=0, voters=[]), RotateEpoch(num=1, voters=[b'a'])
]
params["normal"]["votes"] = [
    DefaultVote(b'v0', data_id=b'd1', commit_id=b'', voter_id=b'a', epoch_num=1, round_num=0),
    DefaultVote(b'v1', data_id=b'd2', commit_id=b'd0', voter_id=b'a', epoch_num=1, round_num=1),
]
params["normal"]["datums"] = [
    DefaultData(b'd0', prev_id=b'', proposer_id=b'', number=0, epoch_num=0, round_num=0, prev_votes=()),
    DefaultData(b'd1', prev_id=b'd0', proposer_id=b'a', number=1, epoch_num=1, round_num=0, prev_votes=()),
    DefaultData(b'd2', prev_id=b'd1', proposer_id=b'a', number=2, epoch_num=1, round_num=1, prev_votes=(params["normal"]["votes"][0],)),
    DefaultData(b'd3', prev_id=b'd2', proposer_id=b'a', number=3, epoch_num=1, round_num=2, prev_votes=(params["normal"]["votes"][1],))
]
params["normal"]["results"] = [
    RoundEndEvent(True, epoch_num=0, round_num=0, candidate_id=b'd0', commit_id=b''),
    RoundEndEvent(True, epoch_num=1, round_num=0, candidate_id=b'd1', commit_id=b'd0'),
    RoundEndEvent(True, epoch_num=1, round_num=1, candidate_id=b'd2', commit_id=b'd1'),
]


params["lazy"] = {}
params["lazy"]["epochs"] = [
    RotateEpoch(num=0, voters=[]), RotateEpoch(num=1, voters=[b'a'])
]
params["lazy"]["votes"] = [
    DefaultVoteFactory(b'').create_lazy_vote(voter_id=b'a', epoch_num=1, round_num=0),
    DefaultVoteFactory(b'').create_lazy_vote(voter_id=b'a', epoch_num=1, round_num=1),
    DefaultVote(b'v0', data_id=b'd1', commit_id=b'd0', voter_id=b'a', epoch_num=1, round_num=3),
]
params["lazy"]["datums"] = [
    DefaultData(b'd0', prev_id=b'', proposer_id=b'', number=0, epoch_num=0, round_num=0, prev_votes=()),
    DefaultDataFactory(b'').create_lazy_data(epoch_num=1, round_num=0, proposer_id=b'a'),
    DefaultDataFactory(b'').create_lazy_data(epoch_num=1, round_num=1, proposer_id=b'a'),
    DefaultDataFactory(b'').create_lazy_data(epoch_num=1, round_num=2, proposer_id=b'a'),
    DefaultData(b'd1', prev_id=b'd0', proposer_id=b'a', number=1, epoch_num=1, round_num=3, prev_votes=()),
]
params["lazy"]["results"] = [
    RoundEndEvent(True, epoch_num=0, round_num=0, candidate_id=b'd0', commit_id=b''),
    RoundEndEvent(False, epoch_num=1, round_num=0, candidate_id=None, commit_id=None),
    RoundEndEvent(False, epoch_num=1, round_num=1, candidate_id=None, commit_id=None),
    RoundEndEvent(True, epoch_num=1, round_num=3, candidate_id=b'd1', commit_id=b'd0'),
]


params["none"] = {}
params["none"]["epochs"] = [
    RotateEpoch(num=0, voters=[]), RotateEpoch(num=1, voters=[b'a'])
]
params["none"]["votes"] = [
    DefaultVoteFactory(b'a').create_none_vote(epoch_num=1, round_num=0),
    DefaultVote(b'v0', data_id=b'd1', commit_id=b'd0', voter_id=b'a', epoch_num=1, round_num=3),
]
params["none"]["datums"] = [
    DefaultData(b'd0', prev_id=b'', proposer_id=b'', number=0, epoch_num=0, round_num=0, prev_votes=()),
    DefaultDataFactory(b'').create_none_data(epoch_num=1, round_num=0, proposer_id=b'a'),
    DefaultDataFactory(b'').create_none_data(epoch_num=1, round_num=1, proposer_id=b'a'),
    DefaultDataFactory(b'').create_none_data(epoch_num=1, round_num=2, proposer_id=b'a'),
    DefaultData(b'd1', prev_id=b'd0', proposer_id=b'a', number=1, epoch_num=1, round_num=3, prev_votes=()),
]
params["none"]["results"] = [
    RoundEndEvent(True, epoch_num=0, round_num=0, candidate_id=b'd0', commit_id=b''),
    RoundEndEvent(False, epoch_num=1, round_num=0, candidate_id=None, commit_id=None),
    RoundEndEvent(True, epoch_num=1, round_num=3, candidate_id=b'd1', commit_id=b'd0'),
]


params["resume"] = {}
params["resume"]["epochs"] = [
    RotateEpoch(num=1, voters=[b'a'])
]
params["resume"]["votes"] = [
    DefaultVote(b'v0', data_id=b'd0', commit_id=b'', voter_id=b'a', epoch_num=1, round_num=10),
    DefaultVoteFactory(b'a').create_none_vote(epoch_num=1, round_num=12),
    DefaultVoteFactory(b'a').create_lazy_vote(voter_id=b'a', epoch_num=1, round_num=14),
    DefaultVote(b'v1', data_id=b'd1', commit_id=b'd0', voter_id=b'a', epoch_num=1, round_num=16),
]
params["resume"]["datums"] = [
    DefaultData(b'd0', prev_id=b'', proposer_id=b'a', number=1, epoch_num=1, round_num=10, prev_votes=()),
    DefaultDataFactory(b'').create_none_data(epoch_num=1, round_num=12, proposer_id=b'a'),
    DefaultDataFactory(b'').create_lazy_data(epoch_num=1, round_num=14, proposer_id=b'a'),
    DefaultData(b'd1', prev_id=b'd0', proposer_id=b'a', number=1, epoch_num=1, round_num=16, prev_votes=(params["resume"]["votes"][0],)),
]
params["resume"]["results"] = [
    RoundEndEvent(True, epoch_num=1, round_num=10, candidate_id=b'd0', commit_id=b''),
    RoundEndEvent(False, epoch_num=1, round_num=12, candidate_id=None, commit_id=None),
    RoundEndEvent(False, epoch_num=1, round_num=14, candidate_id=None, commit_id=None),
    RoundEndEvent(True, epoch_num=1, round_num=16, candidate_id=b'd1', commit_id=b'd0'),
]

epoch_params = [param["epochs"] for param in params.values()]
data_params = [param["datums"] for param in params.values()]
vote_params = [param["votes"] for param in params.values()]
results_params = [param["results"] for param in params.values()]


@pytest.mark.asyncio
@pytest.mark.parametrize("epochs,datums,votes,results",
                         zip(epoch_params, data_params, vote_params, results_params))
async def test_initialize(epochs, datums, votes, results):
    event_system, consensus = await setup_consensus()

    commit_id = datums[0].prev_id
    random.shuffle(epochs)
    random.shuffle(votes)
    random.shuffle(datums)
    await consensus.initialize(commit_id=commit_id, epoch_pool=epochs, data_pool=datums, vote_pool=votes)

    verify(event_system, results)


async def setup_consensus():
    node_id = b'x'
    event_system = MagicMock(EventSystem())
    data_factory = MagicMock(DefaultDataFactory(node_id))
    vote_factory = MagicMock(DefaultVoteFactory(node_id))
    consensus = Consensus(event_system, node_id=node_id, data_factory=data_factory, vote_factory=vote_factory)
    return event_system, consensus


def verify(event_system, results):
    call_args_list = event_system.simulator.raise_event.call_args_list
    assert len(call_args_list) == len(results)
    for args, result in zip(call_args_list, results):
        round_end = args[0][0]
        assert round_end == result
