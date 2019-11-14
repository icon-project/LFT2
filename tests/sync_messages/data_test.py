import os
import random
from lft.app.data import DefaultData
from lft.consensus.layers.sync import SyncMessages


def test_data():
    sync_messages = SyncMessages()
    assert not sync_messages.datums

    data = _random_data()
    sync_messages.add_data(data)

    assert sync_messages.datums
    assert sync_messages.get_data(data.id) is data
    assert sync_messages.get_data(os.urandom(16)) is None
    assert sync_messages.get_data(os.urandom(16), default="default") == "default"

    assert data in sync_messages
    assert not (_random_data() in sync_messages)
    assert data.id not in sync_messages
    assert not(data.id in sync_messages)

    for datum_id, datum in sync_messages.datums:
        assert datum_id == data.id
        assert datum is data


def _random_data():
    return DefaultData(id_=os.urandom(16),
                       prev_id=os.urandom(16),
                       proposer_id=os.urandom(16),
                       number=random.randint(0, 100),
                       term_num=random.randint(0, 100),
                       round_num=random.randint(0, 100))
