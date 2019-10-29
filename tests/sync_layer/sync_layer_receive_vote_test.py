import asyncio
import random
import pytest
from lft.consensus.layers.sync_layer import TIMEOUT_VOTE
from lft.consensus.events import ReceivedVoteEvent
from lft.consensus.exceptions import InvalidTerm, InvalidRound, AlreadyVoted, AlreadyVoteReceived
from tests.sync_layer.setup_sync_layer import setup_sync_layers, get_event


@pytest.mark.asyncio
async def test_sync_layer_invalid_term():
    term_num = 0
    round_num = 0
    voter_num = 7

    genesis_data, voters, event_systems, sync_layers, data_factories, vote_factories = await setup_items(round_num,
                                                                                                          voter_num)
    sync_layer = sync_layers[0]
    vote = await vote_factories[0].create_vote(b'test', genesis_data.id, term_num + 1, 0)
    with pytest.raises(InvalidTerm):
        await sync_layer._receive_vote(vote)

    for sync_layer in sync_layers:
        sync_layer.close()
    for event_system in event_systems:
        event_system.close()


@pytest.mark.asyncio
async def test_sync_layer_invalid_term():
    round_num = 0
    voter_num = 7

    genesis_data, voters, event_systems, sync_layers, data_factories, vote_factories = await setup_items(round_num,
                                                                                                          voter_num)
    sync_layer = sync_layers[0]
    vote = await vote_factories[0].create_vote(b'test', genesis_data.id, 0, round_num + 1)
    with pytest.raises(InvalidRound):
        await sync_layer._receive_vote(vote)

    for sync_layer in sync_layers:
        sync_layer.close()
    for event_system in event_systems:
        event_system.close()


@pytest.mark.asyncio
async def test_sync_layer_already_vote():
    round_num = 0
    voter_num = 7
    genesis_data, voters, event_systems, sync_layers, data_factories, vote_factories = await setup_items(round_num,
                                                                                                          voter_num)

    sync_layer = sync_layers[0]
    vote = await vote_factories[0].create_vote(b'test', genesis_data.id, 0, round_num)
    await sync_layer._receive_vote(vote)

    same_vote = await vote_factories[0].create_vote(b'test', genesis_data.id, 0, round_num)
    with pytest.raises(AlreadyVoted):
        await sync_layer._receive_vote(same_vote)
    same_vote._id = b'1'
    await sync_layer._receive_vote(same_vote)

    none_vote = await vote_factories[0].create_none_vote(0, round_num)
    await sync_layer._receive_vote(none_vote)

    same_none_vote = await vote_factories[0].create_none_vote(0, round_num)
    with pytest.raises(AlreadyVoted):
        await sync_layer._receive_vote(same_none_vote)
    same_none_vote._id = b'3'
    await sync_layer._receive_vote(same_none_vote)

    for sync_layer in sync_layers:
        sync_layer.close()
    for event_system in event_systems:
        event_system.close()


@pytest.mark.asyncio
async def test_sync_layer_already_vote_received():
    round_num = 0
    voter_num = 7
    genesis_data, voters, event_systems, sync_layers, data_factories, vote_factories = await setup_items(round_num,
                                                                                                          voter_num)

    sync_layer = sync_layers[0]

    vote = await vote_factories[1].create_vote(b'test', b'', 0, round_num)
    await sync_layer._receive_vote(vote)

    not_vote = await vote_factories[1].create_not_vote(voters[1], 0, round_num)
    with pytest.raises(AlreadyVoteReceived):
        await sync_layer._receive_vote(not_vote)

    for sync_layer in sync_layers:
        sync_layer.close()
    for event_system in event_systems:
        event_system.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("voter_num", range(4, 10))
async def test_sync_layer_reach_quorum(voter_num: int):
    round_num = 0
    genesis_data, voters, event_systems, sync_layers, data_factories, vote_factories = await setup_items(round_num,
                                                                                                          voter_num)
    sync_layer = sync_layers[0]

    event_systems[0].simulator.stop()
    get_event(event_systems[0])
    get_event(event_systems[0])

    random.shuffle(vote_factories)
    quorum_vote_factories = vote_factories[:sync_layer._term.quorum_num]
    for vote_factory in quorum_vote_factories[:-1]:
        vote = await vote_factory.create_vote(genesis_data.id, genesis_data.prev_id, 0, round_num)
        await sync_layer._receive_vote(vote)

    await asyncio.sleep(TIMEOUT_VOTE + 0.1)
    with pytest.raises(asyncio.QueueEmpty):
        get_event(event_systems[0])

    none_vote = await vote_factories[-1].create_none_vote(0, round_num)
    await sync_layer._receive_vote(none_vote)
    event_systems[0].simulator.stop()

    await asyncio.sleep(TIMEOUT_VOTE + 0.1)

    for _ in range(voter_num):
        event = get_event(event_systems[0])
        assert isinstance(event, ReceivedVoteEvent)
        assert event.vote.is_not()

    with pytest.raises(asyncio.QueueEmpty):
        get_event(event_systems[0])

    for sync_layer in sync_layers:
        sync_layer.close()
    for event_system in event_systems:
        event_system.close()


async def setup_items(round_num: int, voter_num: int):
    voters, event_systems, sync_layers, data_factories, vote_factories = await setup_sync_layers(voter_num)

    index = 0
    sync_layer = sync_layers[index]
    genesis_data = await data_factories[0].create_data(0, b'', 0, round_num, [])

    await sync_layer.initialize(0, round_num, genesis_data, [], voters)
    return genesis_data, voters, event_systems, sync_layers, data_factories, vote_factories
