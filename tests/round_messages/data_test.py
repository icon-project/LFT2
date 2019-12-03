import os
import random
from lft.app.data import DefaultData
from lft.consensus.round import RoundMessages


def test_data():
    round_messages = RoundMessages()
    assert not round_messages.datums

    data = _random_data()
    round_messages.add_data(data)

    assert round_messages.datums
    assert round_messages.get_data(data.id) is data
    assert round_messages.get_data(os.urandom(16)) is None
    assert round_messages.get_data(os.urandom(16), default="default") == "default"

    assert data in round_messages
    assert not (_random_data() in round_messages)
    assert data.id not in round_messages
    assert not(data.id in round_messages)

    for datum_id, datum in round_messages.datums:
        assert datum_id == data.id
        assert datum is data


def _random_data():
    return DefaultData(id_=os.urandom(16),
                       prev_id=os.urandom(16),
                       proposer_id=os.urandom(16),
                       number=random.randint(0, 100),
                       epoch_num=random.randint(0, 100),
                       round_num=random.randint(0, 100))
