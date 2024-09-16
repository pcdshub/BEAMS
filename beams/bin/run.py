"""
`beams run` runs a behavior tree given a configuration file
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from beams.tree_config import get_tree_from_path

logger = logging.getLogger(__name__)


DESCRIPTION = __doc__


def build_arg_parser(argparser=None):
    if argparser is None:
        argparser = argparse.ArgumentParser()

    argparser.description = DESCRIPTION
    argparser.formatter_class = argparse.RawTextHelpFormatter

    argparser.add_argument(
        "filepath",
        type=str,
        help="Behavior Tree configuration filepath"
    )


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
