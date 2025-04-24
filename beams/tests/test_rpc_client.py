from unittest.mock import patch

import pytest

from beams.service.rpc_client import RPCClient


class MockStub:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def enqueue_command(self, *args, **kwargs):
        return f"command queued {args, kwargs}"

    def request_heartbeat(self, *args, **kwargs):
        return "heartbeat requested"


@pytest.fixture(scope="function")
def client() -> RPCClient:
    cl = RPCClient()

    return cl


@patch("beams.service.rpc_client.BEAMS_rpcStub", MockStub)
def test_heartbeat(client: RPCClient):
    client.get_heartbeat()
    assert client.response == "heartbeat requested"


@patch("beams.service.rpc_client.BEAMS_rpcStub", MockStub)
@pytest.mark.parametrize("command,kwargs", [
    ("START_TREE", {"tree_name": "my_tree"}),
    ("TICK_TREE", {"tree_name": "my_tree"}),
    ("PAUSE_TREE", {"tree_name": "my_tree"}),
    ("UNLOAD_TREE", {"tree_name": "my_tree"}),
    ("LOAD_NEW_TREE", {"tree_name": "my_tree", "new_tree_filepath": "a/b/c",
                       "tick_config": "CONTINUOUS", "tick_delay_ms": 42}),
    ("ACK_NODE", {"tree_name": "my_tree", "node_name": "that_node", "user": "me"}),
])
def test_command_no_stub(client: RPCClient, command: str, kwargs):
    method = getattr(client, f"{command.lower()}")
    method(**kwargs)
    assert "queued" in client.response
    assert "command" in client.response


@patch("beams.service.rpc_client.BEAMS_rpcStub", MockStub)
@pytest.mark.parametrize("command,kwargs", [
    ("START_TREE", {"tree_name": "my_tree"}),
    ("TICK_TREE", {"tree_name": "my_tree"}),
    ("PAUSE_TREE", {"tree_name": "my_tree"}),
    ("UNLOAD_TREE", {"tree_name": "my_tree"}),
    ("LOAD_NEW_TREE", {"tree_name": "my_tree", "new_tree_filepath": "a/b/c",
                       "tick_config": "CONTINUOUS", "tick_delay_ms": 42}),
    ("ACK_NODE", {"tree_name": "my_tree", "node_name": "that_node", "user": "me"}),
])
def test_command_with_stub(client: RPCClient, command: str, kwargs):
    method = getattr(client, f"{command.lower()}")
    stub = MockStub()
    method(stub=stub, **kwargs)
    assert "queued" in client.response
    assert "command" in client.response
