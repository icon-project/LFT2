import pytest

from lft.app.data import DefaultData
from tests.consensus.setup_consensus import setup_consensus


@pytest.mark.asyncio
async def test_receive_invalid_proposer_data():
    # GIVEN
    consensus, voters, vote_factories, epoch, genesis_data = await setup_consensus()

    # WHEN
    invalid_proposer_data = DefaultData(
        id_=b'invalid',
        prev_id=genesis_data.id,
        proposer_id=voters[1],
        number=1,
        epoch_num=1,
        round_num=0,
        prev_votes=[]
    )
    consensus.receive_data(invalid_proposer_data)

    # THEN
    with pytest.raises(KeyError):
        consensus._data_pool.get_data(b'invalid')


@pytest.mark.asyncio
async def test_receive_invalid_voter():
    pass


@pytest.mark.ayncio
async def test_receive_invalid_prev_voter():
    pass


@pytest.mark.ayncio
async def test_receive_past_round():
    pass


@pytest.mark.asyncio
async def test_receive_past_epoch():
    pass


@pytest.mark.asyncio
async def test_receive_future_epoch():
    pass

