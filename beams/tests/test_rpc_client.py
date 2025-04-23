from unittest.mock import patch

import pytest


class MockStub:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def enqueue_command(self, *args, **kwargs):
        return f"command queued {args, kwargs}"

    def request_heartbeat(self, *args, **kwargs):
        return "heartbeat requested"


# Mock the rpc stub before it is loaded into the Client class
patch("beams.service.remote_calls.beams_rpc_pb2_grpc.BEAMS_rpcStub", MockStub).start()


from beams.service.rpc_client import RPCClient  # NOQA: E402


@pytest.fixture(scope="function")
def client() -> RPCClient:
    cl = RPCClient()

    return cl


def test_heartbeat(client: RPCClient):
    client._get_heartbeat()
    assert client.response == "heartbeat requested"


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
    method = getattr(client, f"_{command.lower()}")
    method(**kwargs)
    assert "queued" in client.response
    assert "command" in client.response


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
    method = getattr(client, f"_{command.lower()}")
    stub = MockStub()
    method(stub=stub, **kwargs)
    assert "queued" in client.response
    assert "command" in client.response
