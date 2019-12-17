import asyncio
from pathlib import Path
from typing import Optional

import pytest

from lft.app import RecordApp
from lft.consensus.messages.data import Data
from tests.byzantine.double_propoer import DoubleProposer
from tests.byzantine.double_voter import DoubleVoter


@pytest.mark.asyncio
@pytest.mark.parametrize("node_num,duration,expected_min_number", [(4, 100, 50)])
async def test_normal_scenario(node_num, duration, expected_min_number):

    app = RecordApp(node_num, Path("integration_test"))
    app.nodes = app._gen_nodes()
    app._connect_nodes()
    app._start(app.nodes)

    await asyncio.sleep(duration)

    await stop_nodes(app)

    await verify_commit_datums(app.nodes, expected_min_number)


@pytest.mark.asyncio
@pytest.mark.parametrize("node_num,stop_num,duration,expected_min_num", [(4, 1, 100, 50)])
async def test_with_stop_nodes(node_num, stop_num, duration, expected_min_num):
    app = RecordApp(node_num, Path("integration_test"))
    app.nodes = app._gen_nodes()

    non_fault_num = node_num - stop_num

    app._connect_nodes()
    for node in app.nodes[non_fault_num - 1:]:
        node.event_system.stop()
    app._start(app.nodes)
    await asyncio.sleep(duration)

    await stop_nodes(app)

    await verify_commit_datums(app.nodes[:non_fault_num], expected_min_num)
    # Restart nodes
    for node in app.nodes[non_fault_num - 1:]:
        node.start(False)
        node.event_system.start()

    await asyncio.sleep(int(duration/10))
    await verify_commit_datums(app.nodes, expected_min_num)


@pytest.mark.asyncio
@pytest.mark.parametrize("node_num,byzantine_num,duration,expected_min_num", [(4, 1, 100, 50)])
async def test_with_byzantine(node_num, byzantine_num, duration, expected_min_num):
    app = RecordApp(node_num, Path("integration_test"))
    app.nodes = app._gen_nodes()
    non_fault_num = node_num - byzantine_num

    app._connect_nodes()
    byzantines = []
    for node in app.nodes[non_fault_num - 1:]:
        bp = DoubleProposer(node)
        bv = DoubleVoter(node)
        byzantines.append(bp)
        byzantines.append(bv)
        bp.start()
        bv.start()

    app._start(app.nodes)

    await asyncio.sleep(duration)

    await stop_nodes(app)

    await verify_commit_datums(app.nodes, expected_min_num)


async def verify_commit_datums(nodes, expected_number):
    min_commit = (99, 9999999999)
    max_commit = (99, 0)
    for i, node in enumerate(nodes):
        last_number = max(node.commit_datums.keys())
        prev_data = None  # type: Optional[Data]
        for number in range(last_number + 1):
            data = node.commit_datums[number]
            if prev_data:
                assert prev_data.number + 1 == data.number
                assert prev_data.id == data.prev_id
            prev_data = data

        min_commit = (i, last_number) if last_number < min_commit[1] else min_commit
        max_commit = (i, last_number) if last_number > max_commit[1] else max_commit
    assert max_commit[1] - min_commit[1] < 5
    assert max_commit[1] > expected_number
    for node in nodes:
        assert nodes[min_commit[0]].commit_datums[min_commit[1] - 1] == node.commit_datums[min_commit[1] - 1]


async def stop_nodes(app):
    for node in app.nodes:
        node.close()
