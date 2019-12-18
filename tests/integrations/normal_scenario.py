import asyncio
from pathlib import Path
from typing import Optional

import pytest

from lft.app import RecordApp
from lft.consensus.messages.data import Data
from tests.byzantine.double_propoer import DoubleProposer
from tests.byzantine.double_voter import DoubleVoter


@pytest.mark.asyncio
@pytest.mark.parametrize("non_fault_num,stop_num,byzantine_num,duration,min_data_number",
                         [(4, 0, 0, 100, 50),
                          (3, 1, 0, 100, 50),
                          (3, 0, 1, 100, 50)])
async def test_run_nodes(non_fault_num, stop_num, byzantine_num, duration, min_data_number):
    # GIVEN
    node_num = non_fault_num + stop_num + byzantine_num

    app = RecordApp(node_num, Path("integration_test"))
    app.nodes = app._gen_nodes()
    app._connect_nodes()

    await setup_stops(app.nodes, non_fault_num, stop_num)
    await setup_byzantines(app.nodes, byzantine_num)

    # WHEN
    app._start(app.nodes)
    await asyncio.sleep(duration)

    # THEN
    await stop_nodes(app.nodes[:non_fault_num])
    await stop_nodes(app.nodes[len(app.nodes) - byzantine_num:])
    await verify_commit_datums(app.nodes[:non_fault_num], min_data_number)

    await resume_stops(app.nodes, non_fault_num, stop_num)
    await asyncio.sleep(int(duration/10))

    await stop_nodes(app.nodes[non_fault_num: non_fault_num + stop_num])
    await verify_commit_datums(app.nodes[:non_fault_num + stop_num], min_data_number)


# @pytest.mark.asyncio
# @pytest.mark.parametrize(("non_fault_num,stop_num,byzantine_num,first_duration,first_min_number,"
#                           "second_duration,second_min_num"),
#                          [(3, 2, 1, 100, 50, 100, 100)
#                           ])
# async def test_


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


async def setup_stops(nodes, non_fault_num, stop_num):
    for node in nodes[non_fault_num: non_fault_num + stop_num]:
        node.event_system.simulator.stop()


async def setup_byzantines(nodes, byzantine_num):
    byzantines = []
    for node in nodes[len(nodes) - byzantine_num:]:
        bp = DoubleProposer(node)
        bp.start()
        bv = DoubleVoter(node)
        bv.start()
        byzantines.append((bp, bv))
    return byzantines


async def resume_stops(nodes, non_fault_num, stop_num):
    for node in nodes[non_fault_num: non_fault_num + stop_num]:
        node.event_system.simulator.start(False)


async def stop_nodes(nodes):
    for node in nodes:
        node.close()
