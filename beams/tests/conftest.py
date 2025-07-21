from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from contextlib import contextmanager
from copy import copy
from pathlib import Path
from typing import Callable, Generator

import py_trees.logging
import pytest
from py_trees.behaviour import Behaviour
from py_trees.trees import BehaviourTree

from beams.logging import setup_logging
from beams.service.remote_calls.behavior_tree_pb2 import TickStatus, TreeStatus
from beams.service.rpc_client import RPCClient
from beams.service.rpc_handler import BeamsService


def pytest_configure():
    """
    Regenerate the grpc python files from protos.  This ensures generated
    files exist and are up-to-date for the test suite.  This is itself a test,
    as if rpc files are generated incorrectly, the test suite will fail to
    gather the tests due to import errors.

    This is a specially named function that gets run before pytest gathers the
    tests.  This cannot happen in a fixture, since some tests may try to import
    from the generated python files.
    """
    root_dir = Path(__file__).parent.parent.parent
    subprocess.run(args=["make", "gen_grpc"], cwd=root_dir, check=True)


@pytest.fixture(autouse=True)
def central_logging_setup(caplog):
    # Set pytest debugging level, and capture that output
    # Without this logging calls made after the test may fire after the listener
    # thread is closed.
    caplog.set_level(logging.DEBUG)
    # set debug level in case people are curious
    setup_logging(logging.DEBUG)
    # Set py_trees logging level (not our library)
    py_trees.logging.level = py_trees.logging.Level.DEBUG


@pytest.fixture(autouse=True)
def ca_env_vars():
    # Pick a non-standard port to avoid collisions with same-named prod PVs
    os.environ["EPICS_CA_SERVER_PORT"] = "5066"
    # Only broadcast and get on local if
    os.environ["EPICS_CA_AUTO_ADDR_LIST"] = "NO"
    os.environ["EPICS_CA_ADDR_LIST"] = "localhost"


class BTCleaner:
    """
    Helper to call shutdown early to avoid pytest atexit spam
    """
    nodes: list[Behaviour]
    trees: list[BehaviourTree]

    def __init__(self):
        self.nodes = []
        self.trees = []

    def register(self, node_or_tree: Behaviour | BehaviourTree):
        if isinstance(node_or_tree, Behaviour):
            self.nodes.append(node_or_tree)
        elif isinstance(node_or_tree, BehaviourTree):
            self.trees.append(node_or_tree)
        else:
            raise TypeError("Can only register Behavior and BehaviorTree instances!")

    def clean(self):
        for node in self.nodes:
            node.shutdown()
            for child_node in node.children:
                child_node.shutdown()
        for tree in self.trees:
            tree.shutdown()


@pytest.fixture(scope="function")
def bt_cleaner():
    cleaner = BTCleaner()
    yield cleaner
    cleaner.clean()


@contextmanager
def cli_args(args):
    """
    Context manager for running a block of code with a specific set of
    command-line arguments.
    """
    prev_args = sys.argv
    sys.argv = args
    yield
    sys.argv = prev_args


@contextmanager
def restore_logging():
    """
    Context manager for reverting our logging config after testing a function
    that configures the logging.
    """
    prev_handlers = copy(logging.root.handlers)
    yield
    logging.root.handlers = prev_handlers


@pytest.fixture(scope="function")
def rpc_server() -> Generator[BeamsService, None, None]:
    handler = BeamsService()
    handler.start_work()

    yield handler

    # blocking until handler is joined
    handler.join_all_trees()
    handler.stop_work()


@pytest.fixture(scope="function")
def rpc_client(rpc_server):
    """
    Creates a RPCClient instance, and also starts the a server process to back it
    """
    client = RPCClient()

    assert rpc_server.work_proc.is_alive

    def try_get_heartbeat():
        try:
            client.get_heartbeat()
        except Exception:
            return False
        else:
            return True

    # Wait until the rpc server is ready to receive responses
    # I actually don't know what to wait on, but too fast gives 111 errors
    wait_until(try_get_heartbeat)

    return client


def wait_until(condition: Callable[[], bool], timeout=5, polling_period=0.5):
    start_time = time.monotonic()
    while (time.monotonic() - start_time) < timeout:
        if condition():
            return

        time.sleep(polling_period)

    raise TimeoutError(f"Condition failed to resolve within timeout ({timeout} s)")


def assert_heartbeat_has_n_trees(client: RPCClient, n_entries) -> bool:
    resp1 = client.get_heartbeat()
    return len(resp1.behavior_tree_update) == n_entries


def assert_valid_tick_status_at_idx(client: RPCClient, tree_idx: int) -> bool:
    curr_status = client.get_heartbeat().behavior_tree_update[tree_idx].tick_status
    print(curr_status)
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
