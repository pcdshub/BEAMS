from functools import partial
from itertools import product
from pathlib import Path

import pytest

from beams.bin.main import main
from beams.service.remote_calls.behavior_tree_pb2 import (TickStatus,
                                                          TreeDetails,
                                                          TreeStatus)
from beams.service.remote_calls.generic_message_pb2 import MessageType
from beams.service.remote_calls.heartbeat_pb2 import HeartBeatReply
from beams.service.rpc_client import RPCClient
from beams.service.rpc_handler import BeamsService
from beams.tests.conftest import (ETERNAL_GUARD_PATH,
                                  assert_heartbeat_has_n_trees,
                                  assert_test_status,
                                  assert_valid_tick_status_at_idx, cli_args,
                                  restore_logging, wait_until)


def test_heartbeat(rpc_client: RPCClient):
    resp = rpc_client.run(command="get_heartbeat")

    assert isinstance(resp, HeartBeatReply)
    assert resp.mess_t == MessageType.MESSAGE_TYPE_HEARTBEAT


# Tree interaction fixtures.  The intent here is to provide fixtures that
# interact with the service in different ways with the same content.
# This way we can mix and match interaction modes while asserting the end result
# remains the same.

@pytest.fixture()
def load_tree_client(rpc_client: RPCClient, rpc_server: BeamsService):
    def inner_load(tick_config: str):
        rpc_client.load_new_tree(
            new_tree_filepath=str(ETERNAL_GUARD_PATH),
            tick_config=tick_config,
            tick_delay_ms=100,
            tree_name="my_tree"
        )
        print("loaded via RPCClient")

    return inner_load


@pytest.fixture()
def load_tree_cli():
    def inner_load(tick_config: str):
        # load a tree
        args = ["beams", "client", "load_new_tree", "-m", tick_config,
                "-d", "100", str(ETERNAL_GUARD_PATH), "my_tree"]
        with cli_args(args), restore_logging():
            main()
        print("loaded via cli args")

    return inner_load


def get_uuid_for_name(rpc_client: RPCClient, name: str) -> str:
    hb_info = rpc_client.get_heartbeat()
    for update in hb_info.behavior_tree_update:
        if update.tree_id.name == name:
            uuid = update.tree_id.uuid
            break
        raise ValueError(f"unable to find name ({name}) in heartbeat")
    return uuid


@pytest.fixture()
def start_tree_client_name(rpc_client: RPCClient):
    def inner_start():
        rpc_client.start_tree(tree_name="my_tree")

    return inner_start


@pytest.fixture()
def start_tree_client_uuid(rpc_client: RPCClient):
    def inner_start():
        uuid = get_uuid_for_name(rpc_client=rpc_client, name="my_tree")
        rpc_client.start_tree(tree_uuid=uuid)

    return inner_start


@pytest.fixture()
def start_tree_cli_name():
    def inner_start():
        args = ["beams", "client", "start_tree", "--tree_name", "my_tree"]
        with cli_args(args), restore_logging():
            main()

    return inner_start


@pytest.fixture()
def start_tree_cli_uuid(rpc_client: RPCClient):
    def inner_start():
        uuid = get_uuid_for_name(rpc_client, "my_tree")
        args = ["beams", "client", "start_tree", "--tree_uuid", uuid]
        with cli_args(args), restore_logging():
            main()

    return inner_start


@pytest.fixture()
def pause_tree_client_name(rpc_client: RPCClient):
    def inner_pause():
        rpc_client.pause_tree(tree_name="my_tree")

    return inner_pause


@pytest.fixture()
def pause_tree_client_uuid(rpc_client: RPCClient):
    def inner_pause():
        uuid = get_uuid_for_name(rpc_client, "my_tree")
        rpc_client.pause_tree(tree_uuid=uuid)

    return inner_pause


@pytest.fixture()
def pause_tree_cli_name():
    def inner_pause():
        args = ["beams", "client", "pause_tree", "--tree_name", "my_tree"]
        with cli_args(args), restore_logging():
            main()

    return inner_pause


@pytest.fixture()
def pause_tree_cli_uuid(rpc_client: RPCClient):
    def inner_pause():
        uuid = get_uuid_for_name(rpc_client, "my_tree")
        args = ["beams", "client", "pause_tree", "--tree_uuid", uuid]
        with cli_args(args), restore_logging():
            main()

    return inner_pause


@pytest.fixture()
def tick_tree_client_name(rpc_client: RPCClient):
    def inner_tick():
        rpc_client.tick_tree(tree_name="my_tree")

    return inner_tick


@pytest.fixture()
def tick_tree_client_uuid(rpc_client: RPCClient):
    def inner_tick():
        uuid = get_uuid_for_name(rpc_client, "my_tree")
        rpc_client.tick_tree(tree_uuid=uuid)

    return inner_tick


@pytest.fixture()
def tick_tree_cli_name():
    def inner_tick():
        args = ["beams", "client", "tick_tree", "--tree_name", "my_tree"]
        with cli_args(args), restore_logging():
            main()

    return inner_tick


@pytest.fixture()
def tick_tree_cli_uuid(rpc_client: RPCClient):
    def inner_tick():
        uuid = get_uuid_for_name(rpc_client, "my_tree")
        args = ["beams", "client", "tick_tree", "--tree_uuid", uuid]
        with cli_args(args), restore_logging():
            main()

    return inner_tick


@pytest.fixture()
def assert_tree_loaded(rpc_client: RPCClient, rpc_server: BeamsService):
    def inner_assert():
        wait_until(partial(assert_heartbeat_has_n_trees, rpc_client, 1))
        resp0 = rpc_client.get_heartbeat()
        assert resp0.behavior_tree_update[0].tree_status == TreeStatus.IDLE

        tree_dict = rpc_server.sync_man.get_tree_dict()
        assert len(tree_dict.keys()) == 1
        assert list(tree_dict.keys())[0].name == "my_tree"
        tree_uuid = resp0.behavior_tree_update[0].tree_id.uuid
        assert str(list(tree_dict.keys())[0].uuid) == tree_uuid

    return inner_assert


@pytest.fixture()
def assert_tree_started(rpc_client: RPCClient, rpc_server: BeamsService):
    def inner_assert(desired_status: TreeStatus):
        resp1 = rpc_client.get_heartbeat()
        assert resp1.behavior_tree_update[0].tree_id.name == "my_tree"
        wait_until(partial(assert_valid_tick_status_at_idx, rpc_client, 0))

        wait_until(partial(assert_test_status,
                           rpc_client, "my_tree", desired_status))

        # One day we may learn how to access the synchronized treeticker,
        # and at that point we may verify that the status is correct there
        # as well.

    yield inner_assert


LOAD_TREE_FIXTURE_NAMES = ["load_tree_client", "load_tree_cli"]
START_TREE_FIXTURE_NAMES = ["start_tree_client_name", "start_tree_client_uuid",
                            "start_tree_cli_name", "start_tree_cli_uuid"]
TICK_TREE_FIXTURE_NAMES = ["tick_tree_client_name", "tick_tree_client_uuid",
                           "tick_tree_cli_name", "tick_tree_cli_uuid"]
PAUSE_TREE_FIXTURE_NAMES = ["pause_tree_client_name", "pause_tree_client_uuid",
                            "pause_tree_cli_name", "pause_tree_cli_uuid"]


# Test cases.  These will be parametrized by every possible combinations of
# service interaction fixture.

@pytest.mark.parametrize(
    "load_tree_fn, start_tree_fn,",
    product(
        LOAD_TREE_FIXTURE_NAMES,
        START_TREE_FIXTURE_NAMES,
    )
)
def test_continuous(
    request: pytest.FixtureRequest,
    load_tree_fn: str,  # corresponding to a fixture name
    start_tree_fn: str,  # corresponding to a fixture name
    assert_tree_loaded,
    assert_tree_started,
):
    request.getfixturevalue(load_tree_fn)("CONTINUOUS")
    assert_tree_loaded()
    request.getfixturevalue(start_tree_fn)()
    assert_tree_started(TreeStatus.TICKING)


@pytest.mark.parametrize(
    "load_tree_fn, start_tree_fn, tick_tree_fn",
    product(
        ["load_tree_client"],
        START_TREE_FIXTURE_NAMES,
        TICK_TREE_FIXTURE_NAMES,
    )
)
def test_load_interactive_tree(
    request: pytest.FixtureRequest,
    load_tree_fn: str,
    start_tree_fn: str,
    tick_tree_fn: str,
    rpc_client: RPCClient,
    assert_tree_loaded,
    assert_tree_started,
):
    request.getfixturevalue(load_tree_fn)("INTERACTIVE")
    assert_tree_loaded()
    # start tree, but don't tick
    request.getfixturevalue(start_tree_fn)()

    # Before ticking, nodes do not have valid statuses
    resp0 = rpc_client.get_heartbeat()
    assert resp0.behavior_tree_update[0].tick_status == TickStatus.INVALID
    wait_until(partial(assert_test_status,
                       rpc_client, "my_tree", TreeStatus.WAITING_ACK))

    request.getfixturevalue(tick_tree_fn)()
    assert_tree_started(TreeStatus.WAITING_ACK)


@pytest.mark.parametrize(
    "load_tree_fn, start_tree_fn, pause_tree_fn",
    product(
        ["load_tree_client",],
        ["start_tree_client_name",],
        PAUSE_TREE_FIXTURE_NAMES,
    )
)
def test_pause_tree(
    request: pytest.FixtureRequest,
    rpc_client: RPCClient,
    load_tree_fn: str,
    start_tree_fn: str,
    pause_tree_fn: str,
    assert_tree_loaded,
    assert_tree_started,
):
    request.getfixturevalue(load_tree_fn)("CONTINUOUS")
    assert_tree_loaded()
    request.getfixturevalue(start_tree_fn)()
    assert_tree_started(TreeStatus.TICKING)

    request.getfixturevalue(pause_tree_fn)()
    wait_until(partial(assert_test_status, rpc_client, "my_tree", TreeStatus.IDLE))


@pytest.mark.parametrize(
    "load_tree_fn, start_tree_fn, tick_tree_fn",
    product(
        LOAD_TREE_FIXTURE_NAMES,
        ["start_tree_client_name",],
        TICK_TREE_FIXTURE_NAMES,
    )
)
def test_tree_details(
    request: pytest.FixtureRequest,
    rpc_client: RPCClient,
    load_tree_fn: str,
    start_tree_fn: str,
    tick_tree_fn: str,
    assert_tree_loaded,
    assert_tree_started,
):
    request.getfixturevalue(load_tree_fn)("INTERACTIVE")
    assert_tree_loaded()
    request.getfixturevalue(start_tree_fn)()

    resp0 = rpc_client.get_heartbeat()
    assert resp0.behavior_tree_update[0].tick_status == TickStatus.INVALID
    # tick the tree to get some real statuses
    wait_until(partial(assert_test_status, rpc_client,
                       "my_tree", TreeStatus.WAITING_ACK))

    request.getfixturevalue(tick_tree_fn)()
    assert_tree_started(TreeStatus.WAITING_ACK)

    # check the details
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
