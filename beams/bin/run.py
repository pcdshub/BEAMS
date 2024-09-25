"""
`beams run` runs a behavior tree given a configuration file
"""

from __future__ import annotations

import argparse
import logging

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
    argparser.add_argument(
        "-i", "--interactive",
        action="store_true", default=False,
        help="pause and wait for keypress at each tick",
    )
    argparser.add_argument(
        "-t", "--tick-count",
        dest="tick_count", default=1, type=int,
        help="How many times to tick the tree. Values <=0 mean continuous ticking "
             "(Ctrl+C to terminate tree)"
    )
    argparser.add_argument(
        "-d", "--tick-delay",
        dest="tick_delay", default=0.5, type=float,
        help="Delay time (s) between each tick.  Ignored if interactive mode is enabled"
    )
    argparser.add_argument(
        "--hide-node-status",
        action="store_false", dest="show_node_status", default=True,
        help="Hide individual node status output"
    )
    argparser.add_argument(
        "--hide-tree",
        action="store_false", dest="show_tree", default=True,
        help="Hide tree status summary after each tree tick"
    )
    argparser.add_argument(
        "--show-blackboard",
        action="store_true", dest="show_blackboard", default=False,
        help="Show blackboard status after each tree tick"
    )


def main(*args, **kwargs):
    from beams.bin.run_main import main
    main(*args, **kwargs)
