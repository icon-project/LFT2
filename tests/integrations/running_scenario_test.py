import asyncio
import datetime
import inspect
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

    args = str(list(locals().values()))
    args.replace(" ", "")
    path = create_record_path("test_run_nodes", args)

    app = RecordApp(node_num, path)
    app.nodes = app._gen_nodes()
    app._connect_nodes()

    non_fault_nodes = app.nodes[:non_fault_num]
    stopped_nodes = app.nodes[non_fault_num: non_fault_num + stop_num]
    byzantine_nodes = app.nodes[non_fault_num + stop_num: non_fault_num + stop_num + byzantine_num]

    await setup_stops(stopped_nodes)
    await setup_byzantines(byzantine_nodes)

    # WHEN
    app._start(app.nodes)
    await asyncio.sleep(duration)

    # THEN
    await close_nodes(non_fault_nodes)
    await close_nodes(byzantine_nodes)
    await verify_commit_datums(non_fault_nodes, min_data_number)

    await resume_stops(stopped_nodes)
    await asyncio.sleep(int(duration/10))

    await close_nodes(stopped_nodes)
    non_fault_nodes.extend(stopped_nodes)
    await verify_commit_datums(non_fault_nodes, min_data_number)


@pytest.mark.asyncio
@pytest.mark.parametrize(("non_fault_num,stop_num,byzantine_num,first_duration,first_min_num,stop_duration,"
                          "second_duration,second_min_num"),
                         [(3, 2, 1, 100, 50, 100, 100, 100)
                          ])
async def test_run_networks_with_byzantine_and_stop_network_and_restore_network_again(
        non_fault_num, stop_num, byzantine_num, first_duration,
        first_min_num, stop_duration, second_duration, second_min_num):

    args = str(list(locals().values()))
    args.replace(" ", "")
    path = create_record_path("test_run_networks_with_byzantine_and_stop_network_and_restore_network_again", args)

    app = RecordApp(non_fault_num + byzantine_num, path)

    app.nodes = app._gen_nodes()
    app._connect_nodes()

    non_fault_nodes = app.nodes[:non_fault_num]
    byzantine_nodes = app.nodes[non_fault_num: non_fault_num + byzantine_num]
    await setup_byzantines(byzantine_nodes)

    app._start(app.nodes)
    await asyncio.sleep(first_duration)
    await setup_stops(app.nodes)
    commit_number = await verify_commit_datums(non_fault_nodes, first_min_num)

    stopped_nodes = app.nodes[:stop_num]
    await resume_stops(app.nodes[stop_num:])
    await asyncio.sleep(stop_duration)

    await resume_stops(stopped_nodes)
    await asyncio.sleep(second_duration)

    await close_nodes(app.nodes)
    await verify_commit_datums(non_fault_nodes, max(second_min_num, commit_number))


async def verify_commit_datums(nodes, expected_number):
    min_commit = (99, 9999999999)
    max_commit = (99, 0)
    for i, node in enumerate(nodes):
        last_number = max(node.commit_datums.keys())
        prev_data: Optional[Data] = None
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

    return max_commit[1]


def create_record_path(test_name, params) -> Path:
    now = datetime.datetime.now()
    now_str = now.strftime('%Y-%m-%d-%H:%M:%S')
    return Path(f"{test_name}/{now_str}/{params}")


async def setup_stops(nodes):
    for node in nodes:
        node.event_system.simulator.stop()


async def setup_byzantines(nodes):
    byzantines = []
    for node in nodes:
        bp = DoubleProposer(node)
        bp.start()
        bv = DoubleVoter(node)
        bv.start()
        byzantines.append((bp, bv))
    return byzantines


async def resume_stops(nodes):
    for node in nodes:
        node.event_system.simulator.start(False)


async def close_nodes(nodes):
    for node in nodes:
        node.close()
