"""
This module defines a config file format for beams clients and services.

The server and the client can use the same config file.

The config file is the basic configparser/ini format and may look
something like:

beams.cfg

[DEFAULT]
server_host = my-favorite-server
server_port = 5001
"""

import configparser
import dataclasses
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class BeamsConfig:
    server_host: str
    server_port: int


def find_config() -> str:
    """
    Return the directory that contains the user's beams.cfg file.
    """
    # Environment variable first
    beams_cfg = os.environ.get("BEAMS_CFG", "")
    if beams_cfg:
        logger.debug("Found $BEAMS_CFG specification at %s", beams_cfg)
        return beams_cfg
    # Working directory next
    config_dirs = ["."]
    # General config directories last
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config is not None:
        config_dirs.append(xdg_config)
    config_dirs.append(os.path.expanduser("~/.config"))
    for directory in config_dirs:
        logger.debug("Searching for Beams config in %s", directory)
        full_path = os.path.join(directory, "beams.cfg")
        if os.path.exists(full_path):
            logger.debug("Found configuration file at %r", full_path)
            return full_path
    # Give up
    raise OSError("No beams configuration file found. Check BEAMS_CFG.")


def load_config(config: Optional[str] = None) -> BeamsConfig:
    """
    Get the beams configuration.
    """
    if config is None:
        config = find_config()
    config_parser = configparser.ConfigParser()
    files_read = config_parser.read(config)
    if not files_read:
        raise OSError(f"Cannot read config file {config}")
    return BeamsConfig(
        server_host=config_parser["DEFAULT"]["server_host"],
        server_port=int(config_parser["DEFAULT"]["server_port"]),
    )
