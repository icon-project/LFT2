import os
import pytest
from typing import Tuple
from mock import MagicMock
from lft.app.data import DefaultDataFactory, DefaultData
from lft.app.vote import DefaultVoteFactory
from lft.app.epoch import RotateEpoch
from lft.consensus.messages.vote import Vote
from lft.event import EventSystem
from lft.consensus import Consensus
from lft.consensus.messages.data import Data
from lft.consensus.events import RoundEndEvent


@pytest.mark.asyncio
async def test_candidate_change_by_vote():
    event_system, consensus, genesis_data = await setup_consensus()

    # Genesis(E0R0) -> Data10(E1R0)
    data10 = await new_and_receive_data(consensus=consensus,
                                        candidate=genesis_data,
                                        new_epoch_num=1,
                                        new_round_num=0)
    event_system.simulator.raise_event.assert_not_called()

    await new_and_receive_votes(consensus=consensus,
                                data=data10)
    event_system.simulator.raise_event.assert_called_once()

    round_end_event = event_system.simulator.raise_event.call_args_list[0][0][0]
    verify_round_end_event(round_end_event, data10)
    event_system.simulator.raise_event.reset_mock()

    # Genesis(E0R0) -> Data11(E1R1)
    data11 = await new_and_receive_data(consensus=consensus,
                                        candidate=genesis_data,
                                        new_epoch_num=1,
                                        new_round_num=1)
    event_system.simulator.raise_event.assert_not_called()

    await new_and_receive_votes(consensus=consensus,
                                data=data11)
    event_system.simulator.raise_event.assert_called_once()

    round_end_event = event_system.simulator.raise_event.call_args_list[0][0][0]
    verify_round_end_event(round_end_event, data11)


@pytest.mark.asyncio
async def test_candidate_change_by_data():
    event_system, consensus, genesis_data = await setup_consensus()

    # Genesis(E0R0) -> Data10(E1R0)
    data10 = await new_and_receive_data(consensus=consensus,
                                        candidate=genesis_data,
                                        new_epoch_num=1,
                                        new_round_num=0)
    event_system.simulator.raise_event.assert_not_called()

    await new_and_receive_votes(consensus=consensus,
                                data=data10)
    event_system.simulator.raise_event.assert_called_once()

    round_end_event = event_system.simulator.raise_event.call_args_list[0][0][0]
    verify_round_end_event(round_end_event, data10)
    event_system.simulator.raise_event.reset_mock()

    # Genesis(E0R0) -> Data11(E1R1)
    data11 = await new_and_receive_data(consensus=consensus,
                                        candidate=genesis_data,
                                        new_epoch_num=1,
                                        new_round_num=1)
    event_system.simulator.raise_event.assert_not_called()

    # Candidate11(E1R1) -> Data12(E1R2)
    data12 = await new_and_receive_data(consensus=consensus,
                                        candidate=data11,
                                        new_epoch_num=1,
                                        new_round_num=2)
    round_end_event = event_system.simulator.raise_event.call_args_list[0][0][0]
    verify_round_end_event(round_end_event, data11)
    event_system.simulator.raise_event.reset_mock()


@pytest.mark.asyncio
async def test_candidate_change_recursively():
    event_system, consensus, genesis_data = await setup_consensus()

    data10 = await new_data(consensus=consensus,
                            candidate=genesis_data,
                            new_epoch_num=1,
                            new_round_num=0)
    data11 = await new_data(consensus=consensus,
                            candidate=data10,
                            new_epoch_num=1,
                            new_round_num=1)
    data12 = await new_data(consensus=consensus,
                            candidate=data11,
                            new_epoch_num=1,
                            new_round_num=2)
    data13 = await new_data(consensus=consensus,
                            candidate=data12,
                            new_epoch_num=1,
                            new_round_num=3)
    data14 = await new_data(consensus=consensus,
                            candidate=data13,
                            new_epoch_num=1,
                            new_round_num=4)

    await receive_data(consensus, data10)
    await receive_data(consensus, data12)
    await receive_data(consensus, data14)

    votes12 = await new_votes(consensus, data12)
    await receive_votes(consensus, votes12)
    event_system.simulator.raise_event.assert_not_called()

    await receive_data(consensus, data11)

    assert len(event_system.simulator.raise_event.call_args_list) == 3

    round_end_event10 = event_system.simulator.raise_event.call_args_list[0][0][0]
    verify_round_end_event(round_end_event10, data10)

    round_end_event11 = event_system.simulator.raise_event.call_args_list[1][0][0]
    verify_round_end_event(round_end_event11, data11)

    round_end_event12 = event_system.simulator.raise_event.call_args_list[2][0][0]
    verify_round_end_event(round_end_event12, data12)


async def new_data(consensus: Consensus, candidate: Data, new_epoch_num: int, new_round_num: int):
    epoch = consensus._epoch_pool.get_epoch(new_epoch_num)
    proposer = epoch.get_proposer_id(new_round_num)
    data_factory = DefaultDataFactory(proposer)

    prev_votes = await new_votes(consensus, candidate)
    return await data_factory.create_data(candidate.number + 1, candidate.id, epoch.num, new_round_num, prev_votes)


async def new_and_receive_data(consensus: Consensus, candidate: Data, new_epoch_num: int, new_round_num: int):
    data = await new_data(consensus, candidate, new_epoch_num, new_round_num)
    await receive_data(consensus, data)
    return data


async def receive_data(consensus: Consensus, data: Data):
    await consensus.receive_data(data)


async def new_votes(consensus: Consensus, data: Data):
    epoch = consensus._epoch_pool.get_epoch(data.epoch_num)
    vote_factories = [
        DefaultVoteFactory(voter) for voter in epoch.voters
    ]
    return tuple([
        await vote_factory.create_vote(data.id, data.prev_id, data.epoch_num, data.round_num)
        for vote_factory in vote_factories
    ])


async def receive_votes(consensus: Consensus, votes: Tuple[Vote, ...]):
    for vote in votes:
        await consensus.receive_vote(vote)


async def new_and_receive_votes(consensus: Consensus, data: Data):
    votes = await new_votes(consensus, data)
    await receive_votes(consensus, votes)
    return votes


def verify_round_end_event(round_end_event: RoundEndEvent, candidate_data: Data):
    assert isinstance(round_end_event, RoundEndEvent)
    assert round_end_event.epoch_num == candidate_data.epoch_num
    assert round_end_event.round_num == candidate_data.round_num
    assert round_end_event.candidate_id == candidate_data.id
    assert round_end_event.commit_id == candidate_data.prev_id


async def setup_consensus():
    node_id = b'x'
    event_system = MagicMock(EventSystem())
    data_factory = DefaultDataFactory(node_id)
    vote_factory = DefaultVoteFactory(node_id)
    consensus = Consensus(event_system, node_id=node_id, data_factory=data_factory, vote_factory=vote_factory)

    voters = [os.urandom(16)]
    epochs = [RotateEpoch(0, []), RotateEpoch(1, voters)]
    datums = [DefaultData(id_=b'genesis', prev_id=b'', proposer_id=b'', number=0, epoch_num=0, round_num=0, prev_votes=())]
    votes = []

    await consensus.initialize(datums[0].prev_id, epochs, datums, votes)
    event_system.simulator.raise_event.reset_mock()

    return event_system, consensus, datums[0]
