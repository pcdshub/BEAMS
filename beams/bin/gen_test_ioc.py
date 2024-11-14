"""
Generate a test caproto IOC containing all the PVs from a tree as they are in the live control system.

Intended usage is something like:
beams gen_test_ioc my_tree.json > outfile.py

You can use this file as-is or edit it for your purposes.

If running in online mode (the default, unless you pass --offline),
this will query the controls system for live starting values and data types.

In offline mode (--offline) everything will start as an int with value 0.
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
        "--offline",
        action="store_true",
        help="Use default values instead of live values. Useful when running offline.",
    )


def main(*args, **kwargs):
    from beams.bin.gen_test_ioc_main import main
    main(*args, **kwargs)
