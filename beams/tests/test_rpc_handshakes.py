from functools import partial
from pathlib import Path

from beams.service.remote_calls.behavior_tree_pb2 import (TickStatus,
                                                          TreeDetails,
                                                          TreeStatus)
from beams.service.remote_calls.generic_message_pb2 import MessageType
from beams.service.remote_calls.heartbeat_pb2 import HeartBeatReply
from beams.service.rpc_client import RPCClient
from beams.tests.conftest import wait_until


def assert_heartbeat_has_n_trees(client: RPCClient, n_entries) -> bool:
    resp1 = client.get_heartbeat()
    return len(resp1.behavior_tree_update) == n_entries


def assert_valid_tick_status_at_idx(client: RPCClient, tree_idx: int) -> bool:
    curr_status = client.get_heartbeat().behavior_tree_update[tree_idx].tick_status
    return curr_status != TickStatus.INVALID


def assert_test_status(rpc_client: RPCClient, name: str, status: TreeStatus) -> bool:
    resp = rpc_client.get_heartbeat()
    my_msg = None
    for update_msg in resp.behavior_tree_update:
        if update_msg.tree_id.name == name:
            my_msg = update_msg

    if my_msg is None:
        return False
    return my_msg.tree_status == status


def test_heartbeat(rpc_client: RPCClient):
    resp = rpc_client.run(command="get_heartbeat")

    assert isinstance(resp, HeartBeatReply)
    assert resp.mess_t == MessageType.MESSAGE_TYPE_HEARTBEAT


def test_load_run_continuous_tree(rpc_client: RPCClient):
    tree_path = Path(__file__).parent / "artifacts" / "eternal_guard.json"
    rpc_client.load_new_tree(
        new_tree_filepath=str(tree_path),
        tick_config="CONTINUOUS",
        tick_delay_ms=100,
        tree_name="my_tree"
    )

    wait_until(partial(assert_heartbeat_has_n_trees, rpc_client, 1))
    resp0 = rpc_client.get_heartbeat()
    assert resp0.behavior_tree_update[0].tree_status == TreeStatus.IDLE
    # tree name taken from json, not our setting

    rpc_client.start_tree("my_tree")

    wait_until(partial(assert_heartbeat_has_n_trees, rpc_client, 1))
    # tree name taken from json, not our setting
    resp1 = rpc_client.get_heartbeat()
    assert resp1.behavior_tree_update[0].tree_id.name == "my_tree"
    wait_until(partial(assert_valid_tick_status_at_idx, rpc_client, 0))

    wait_until(partial(assert_test_status,
                       rpc_client, "my_tree", TreeStatus.TICKING))


def test_load_interactive_tree(rpc_client: RPCClient):
    tree_path = Path(__file__).parent / "artifacts" / "eternal_guard.json"
    rpc_client.load_new_tree(
        new_tree_filepath=str(tree_path),
        tick_config="INTERACTIVE",
        tick_delay_ms=10,
        tree_name="my_tree"
    )

    wait_until(partial(assert_heartbeat_has_n_trees, rpc_client, 1))
    resp0 = rpc_client.get_heartbeat()
    assert resp0.behavior_tree_update[0].tree_status == TreeStatus.IDLE

    # start tree, but don't tick
    rpc_client.start_tree("my_tree")
    wait_until(partial(assert_heartbeat_has_n_trees, rpc_client, 1))
    resp0 = rpc_client.get_heartbeat()
    assert resp0.behavior_tree_update[0].tick_status == TickStatus.INVALID
    wait_until(partial(assert_test_status,
                       rpc_client, "my_tree", TreeStatus.WAITING_ACK))

    # tick tree
    rpc_client.tick_tree("my_tree")
    wait_until(partial(assert_valid_tick_status_at_idx, rpc_client, 0))

    # back to waiting for tick
    wait_until(partial(assert_test_status,
                       rpc_client, "my_tree", TreeStatus.WAITING_ACK))


def test_pause_tree(rpc_client: RPCClient):
    tree_path = Path(__file__).parent / "artifacts" / "eternal_guard.json"
    rpc_client.load_new_tree(
        new_tree_filepath=str(tree_path),
        tick_config="CONTINUOUS",
        tick_delay_ms=10,
        tree_name="my_tree"
    )

    wait_until(partial(assert_test_status, rpc_client, "my_tree", TreeStatus.IDLE))
    rpc_client.start_tree("my_tree")
    wait_until(partial(assert_test_status, rpc_client,
                       "my_tree", TreeStatus.TICKING))
    rpc_client.pause_tree("my_tree")
    wait_until(partial(assert_test_status, rpc_client, "my_tree", TreeStatus.IDLE))


def test_tree_details(rpc_client: RPCClient):
    tree_path = Path(__file__).parent / "artifacts" / "eternal_guard.json"
    rpc_client.load_new_tree(
        new_tree_filepath=str(tree_path),
        tick_config="INTERACTIVE",
        tick_delay_ms=10,
        tree_name="my_tree"
    )

    wait_until(partial(assert_test_status, rpc_client, "my_tree", TreeStatus.IDLE))
    rpc_client.start_tree("my_tree")
    # tick the tree to get some real statuses
    rpc_client.tick_tree("my_tree")
    wait_until(partial(assert_test_status, rpc_client,
                       "my_tree", TreeStatus.WAITING_ACK))

    details = rpc_client.get_detailed_update(tree_name="my_tree")
    assert details.tree_id.name == "my_tree"
    assert details.tree_status == TreeStatus.WAITING_ACK
    assert details.node_info.id.name == "Eternal Guard"
    assert len(details.node_info.children) == 3
    assert details.node_info.children[0].id.name == "Condition 1"


def test_uuid_matching(rpc_client: RPCClient):
    tree_path = Path(__file__).parent / "artifacts" / "eternal_guard.json"
    rpc_client.load_new_tree(
        new_tree_filepath=str(tree_path),
        tick_config="INTERACTIVE",
        tick_delay_ms=10,
        tree_name="eg"
    )
    rpc_client.tick_tree(tree_name="eg")

    tree_path_2 = Path(__file__).parent / "artifacts" / "eggs.json"
    rpc_client.load_new_tree(
        new_tree_filepath=str(tree_path_2),
        tick_config="INTERACTIVE",
        tick_delay_ms=10,
        tree_name="egg"
    )
    rpc_client.tick_tree(tree_name="egg")

    wait_until(lambda: len(rpc_client.get_heartbeat().behavior_tree_update) == 2)
    heartbeat = rpc_client.get_heartbeat()

    for msg in heartbeat.behavior_tree_update:
        print(msg.tree_id)
        name_details = rpc_client.get_detailed_update(tree_name=msg.tree_id.name)
        uuid_details = rpc_client.get_detailed_update(tree_uuid=msg.tree_id.uuid)
        assert isinstance(name_details, TreeDetails)
        assert isinstance(uuid_details, TreeDetails)
        assert name_details == uuid_details
