import pytest
from lft.consensus.events import BroadcastVoteEvent, ReceivedVoteEvent, DoneRoundEvent
from tests.sync_layer.setup_sync_layer import setup_sync_layers, get_event, verify_no_events


@pytest.mark.asyncio
@pytest.mark.parametrize("round_num, voter_num", [(0, i) for i in range(4, 100)])
async def test_sync_layer_not_proposer_ordered(round_num, voter_num: int):
    voters, event_systems, sync_layers, data_factories, vote_factories = await setup_sync_layers(voter_num)

    proposer_index = round_num % voter_num
    proposer_data_factory = data_factories[proposer_index]
    candidate_data = await proposer_data_factory.create_data(0, b'', 0, round_num, [])

    not_proposer_index = (round_num + 1) % voter_num
    not_proposer_sync_layer = sync_layers[not_proposer_index]
    not_proposer_event_system = event_systems[not_proposer_index]

    await not_proposer_sync_layer.initialize(0, round_num, candidate_data, [], voters)

    new_data = await proposer_data_factory.create_data(0, candidate_data.id, 0, round_num, [])
    await not_proposer_sync_layer.receive_data(new_data)

    event = get_event(not_proposer_event_system)
    assert isinstance(event, BroadcastVoteEvent)

    event = get_event(not_proposer_event_system)
    assert isinstance(event, ReceivedVoteEvent)

    for vote_factory in vote_factories:
        vote = await vote_factory.create_vote(new_data.id, candidate_data.id, new_data.term_num, new_data.round_num)
        await not_proposer_sync_layer.receive_vote(vote)

    event = get_event(not_proposer_event_system)
    assert isinstance(event, DoneRoundEvent)

    for sync_layer in sync_layers:
        sync_layer.close()
    for event_system in event_systems:
        event_system.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("round_num, voter_num", [(0, i) for i in range(4, 100)])
async def test_sync_layer_not_proposer_not_ordered(round_num, voter_num: int):
    voters, event_systems, sync_layers, data_factories, vote_factories = await setup_sync_layers(voter_num)

    proposer_index = round_num % voter_num
    proposer_data_factory = data_factories[proposer_index]
    candidate_data = await proposer_data_factory.create_data(0, b'', 0, round_num, [])

    not_proposer_index = (round_num + 1) % voter_num
    not_proposer_sync_layer = sync_layers[not_proposer_index]
    not_proposer_event_system = event_systems[not_proposer_index]

    await not_proposer_sync_layer.initialize(0, round_num, candidate_data, [], voters)

    new_data = await proposer_data_factory.create_data(0, candidate_data.id, 0, round_num, [])
    for vote_factory in vote_factories:
        vote = await vote_factory.create_vote(new_data.id, candidate_data.id, new_data.term_num, new_data.round_num)
        await not_proposer_sync_layer.receive_vote(vote)

    verify_no_events(not_proposer_event_system)

    await not_proposer_sync_layer.receive_data(new_data)

    event = get_event(not_proposer_event_system)
    assert isinstance(event, BroadcastVoteEvent)

    event = get_event(not_proposer_event_system)
    assert isinstance(event, ReceivedVoteEvent)

    event = get_event(not_proposer_event_system)
    assert isinstance(event, DoneRoundEvent)

    for sync_layer in sync_layers:
        sync_layer.close()
    for event_system in event_systems:
        event_system.close()

