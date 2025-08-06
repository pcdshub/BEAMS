import os
from pathlib import Path

import pytest

from beams.config import BeamsConfig, find_config, load_config

SAMPLE_CFG = Path(__file__).parent / "config.cfg"


@pytest.fixture(scope="function")
def xdg_config_patch(tmp_path):
    config_home = tmp_path / "xdg_config_home"
    config_home.mkdir()
    return config_home


@pytest.fixture(scope="function")
def beams_cfg(xdg_config_patch: Path):
    # patch config discovery paths
    xdg_cfg = os.environ.get("XDG_CONFIG_HOME", "")
    beams_cfg_path = os.environ.get("BEAMS_CFG", "")

    os.environ["XDG_CONFIG_HOME"] = str(xdg_config_patch)
    os.environ["BEAMS_CFG"] = ""

    beams_cfg_path = xdg_config_patch / "beams.cfg"
    beams_cfg_path.symlink_to(SAMPLE_CFG)

    yield str(beams_cfg_path)

    # reset env vars
    os.environ["BEAMS_CFG"] = str(beams_cfg_path)
    os.environ["XDG_CONFIG_HOME"] = xdg_cfg


def test_load_config(beams_cfg: str):
    config = load_config(beams_cfg)
    assert config == BeamsConfig(
        host="host",
        port=9999,
    )


def test_find_config(beams_cfg: str):
    assert beams_cfg == str(find_config())

    # explicit BEAMS_CFG env var supercedes XDG_CONFIG_HOME
    os.environ["BEAMS_CFG"] = "other/cfg"
    assert "other/cfg" == str(find_config())
