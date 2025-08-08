import os
from pathlib import Path

import pytest

from beams.config import BeamsConfig, find_config, load_config

SAMPLE_CFG = Path(__file__).parent / "config.cfg"


@pytest.fixture(scope="function")
def beams_cfg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # patch config discovery paths
    config_home = tmp_path / "xdg_config_home"
    config_home.mkdir()

    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))
    if os.environ.get("BEAMS_CFG") is not None:
        monkeypatch.delenv("BEAMS_CFG")

    beams_cfg_path = config_home / "beams.cfg"
    beams_cfg_path.symlink_to(SAMPLE_CFG)

    yield str(beams_cfg_path)


def test_load_config(beams_cfg: str):
    config = load_config(beams_cfg)
    assert config == BeamsConfig(
        host="the-server-name",
        port=9999,
    )


def test_find_config_xdg(beams_cfg: str):
    assert find_config() == beams_cfg


def test_find_config_env_var(beams_cfg: str, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("BEAMS_CFG", "other/cfg")
    assert find_config() == "other/cfg"
