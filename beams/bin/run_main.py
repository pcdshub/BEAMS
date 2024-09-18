"""
Logic for `superscore run` main
"""

import logging
from pathlib import Path

from beams.tree_config import get_tree_from_path

logger = logging.getLogger(__name__)


def main(filepath: str):
    logger.info(f"Running behavior tree at {filepath}")
    # grab config
    fp = Path(filepath).resolve()
    if not fp.is_file():
        raise ValueError("Provided filepath is not a file")

    tree = get_tree_from_path(fp)
    print(tree)
    # TODO: the rest of whatever we determine the "run" process to be
    # run external server?
    # setup tree?
    # tick?
    # settings for ticking? (continuous tick?, as separate process?)
