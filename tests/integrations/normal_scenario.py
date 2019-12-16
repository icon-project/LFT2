import asyncio
from pathlib import Path
from time import sleep

import pytest

from lft.app import RecordApp, App


@pytest.mark.asyncio
@pytest.mark.parametrize("node_num,duration", [(4, 5)])
async def test_normal_scenario(node_num, duration):
    app = RecordApp(node_num, Path("integration_test"))
    app.nodes = app._gen_nodes()

    for node in app.nodes:
        for peer in (peer for peer in app.nodes if peer != node):
            node.register_peer(peer)

    app._start(app.nodes)
    await asyncio.sleep(duration)

    for node in app.nodes:
        print(node.commit_datums)
