import pytest
from lft.consensus.exceptions import AlreadyVoted
from tests.sync_layer.setup_sync_layer import setup_sync_layers


@pytest.mark.asyncio
@pytest.mark.parametrize("round_num, voter_num", [(0, i) for i in range(4, 100)])
async def test_sync_layer_already_vote(round_num, voter_num: int):
    genesis_data, voters, event_systems, sync_layers, data_factories, vote_factories = await setup_items(round_num, voter_num)

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


async def setup_items(round_num: int, voter_num: int):
    voters, event_systems, sync_layers, data_factories, vote_factories = await setup_sync_layers(voter_num)

    index = 0
    sync_layer = sync_layers[index]
    genesis_data = await data_factories[0].create_data(0, b'', 0, round_num, [])

    await sync_layer.initialize(0, round_num, genesis_data, [], voters)
    return genesis_data, voters, event_systems, sync_layers, data_factories, vote_factories
