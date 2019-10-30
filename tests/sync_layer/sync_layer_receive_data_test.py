import asyncio
import pytest
from lft.consensus.events import DoneRoundEvent
from lft.consensus.exceptions import InvalidTerm, InvalidRound, AlreadyProposed, AlreadyDataReceived
from tests.sync_layer.setup_sync_layer import setup_sync_layers, get_event


@pytest.mark.asyncio
async def test_sync_layer_invalid_term():
    term_num = 0
    round_num = 0
    voter_num = 7

    genesis_data, voters, event_systems, sync_layers, data_factories, vote_factories = await setup_items(round_num,
                                                                                                          voter_num)
    sync_layer = sync_layers[0]
    data = await data_factories[0].create_data(0, b'', term_num + 1, 0, [])
    with pytest.raises(InvalidTerm):
        await sync_layer._receive_data(data)

    for sync_layer in sync_layers:
        sync_layer.close()
    for event_system in event_systems:
        event_system.close()


@pytest.mark.asyncio
async def test_sync_layer_invalid_round():
    round_num = 0
    voter_num = 7

    genesis_data, voters, event_systems, sync_layers, data_factories, vote_factories = await setup_items(round_num,
                                                                                                          voter_num)
    sync_layer = sync_layers[0]
    data = await data_factories[0].create_data(0, b'', 0, round_num + 1, [])
    with pytest.raises(InvalidRound):
        await sync_layer._receive_data(data)

    for sync_layer in sync_layers:
        sync_layer.close()
    for event_system in event_systems:
        event_system.close()


@pytest.mark.asyncio
async def test_sync_layer_already_propose():
    round_num = 0
    voter_num = 7

    genesis_data, voters, event_systems, sync_layers, data_factories, vote_factories = await setup_items(round_num,
                                                                                                          voter_num)
    sync_layer = sync_layers[0]
    data = await data_factories[0].create_data(
        genesis_data.number + 1, genesis_data.id, genesis_data.term_num, round_num, []
    )
    await sync_layer._receive_data(data)
    with pytest.raises(AlreadyProposed):
        await sync_layer._receive_data(data)

    for sync_layer in sync_layers:
        sync_layer.close()
    for event_system in event_systems:
        event_system.close()


@pytest.mark.asyncio
async def test_sync_layer_data_received():
    round_num = 0
    voter_num = 7

    genesis_data, voters, event_systems, sync_layers, data_factories, vote_factories = await setup_items(round_num,
                                                                                                          voter_num)
    sync_layer = sync_layers[0]
    data = await data_factories[0].create_data(
        genesis_data.number + 1, genesis_data.id, genesis_data.term_num, round_num, []
    )
    await sync_layer._receive_data(data)
    not_data = await data_factories[0].create_not_data(
        genesis_data.number, genesis_data.term_num, round_num, genesis_data.proposer_id
    )
    with pytest.raises(AlreadyDataReceived):
        await sync_layer._receive_data(not_data)

    for sync_layer in sync_layers:
        sync_layer.close()
    for event_system in event_systems:
        event_system.close()


@pytest.mark.asyncio
async def test_sync_layer_data_vote_sync():
    round_num = 0
    voter_num = 7

    genesis_data, voters, event_systems, sync_layers, data_factories, vote_factories = await setup_items(round_num,
                                                                                                          voter_num)
    get_event(event_systems[0])
    get_event(event_systems[0])

    sync_layer = sync_layers[0]
    data = await data_factories[0].create_data(
        genesis_data.number + 1, genesis_data.id, genesis_data.term_num, round_num, []
    )
    for vote_factory in vote_factories:
        vote = await vote_factory.create_vote(data.id, genesis_data.id, 0, round_num)
        await sync_layer.receive_vote(vote)

    with pytest.raises(asyncio.QueueEmpty):
        get_event(event_systems[0])

    await sync_layer.receive_data(data)
    # Broadcast Data
    get_event(event_systems[0])
    # Received Vote
    get_event(event_systems[0])

    event = get_event(event_systems[0])
    assert isinstance(event, DoneRoundEvent)

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
