import os
from pathlib import Path
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


SAMPLE_CFG = Path(__file__).parent / "config.cfg"


@pytest.fixture(scope='function')
def xdg_config_patch(tmp_path):
    config_home = tmp_path / 'xdg_config_home'
    config_home.mkdir()
    return config_home


@pytest.fixture(scope='function')
def beams_cfg(xdg_config_patch: Path):
    # patch config discovery paths
    xdg_cfg = os.environ.get("XDG_CONFIG_HOME", '')
    beams_cfg_path = os.environ.get("BEAMS_CFG", '')

    os.environ['XDG_CONFIG_HOME'] = str(xdg_config_patch)
    os.environ['BEAMS_CFG'] = ''

    beams_cfg_path = xdg_config_patch / "beams.cfg"
    beams_cfg_path.symlink_to(SAMPLE_CFG)

    yield str(beams_cfg_path)

    # reset env vars
    os.environ["BEAMS_CFG"] = str(beams_cfg_path)
    os.environ["XDG_CONFIG_HOME"] = xdg_cfg


@pytest.fixture(scope="function")
def client() -> RPCClient:
    cl = RPCClient()

    return cl


def test_from_cfg(beams_cfg: str):
    client = RPCClient.from_config()
    assert client.server_address == "my_address:9999"


def test_find_config(beams_cfg: str):
    assert beams_cfg == RPCClient.find_config()

    # explicit BEAMS_CFG env var supercedes XDG_CONFIG_HOME
    os.environ['BEAMS_CFG'] = 'other/cfg'
    assert 'other/cfg' == RPCClient.find_config()


@patch("beams.service.rpc_client.BEAMS_rpcStub", MockStub)
def test_heartbeat(client: RPCClient):
    client.get_heartbeat()
    assert client.last_response == "heartbeat requested"


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
    assert "queued" in client.last_response
    assert "command" in client.last_response


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
    assert "queued" in client.last_response
    assert "command" in client.last_response
