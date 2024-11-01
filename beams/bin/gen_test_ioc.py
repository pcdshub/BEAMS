"""
Generate a test caproto IOC containing all the PVs from a tree set to 0 with no special logic.

Intended usage is something like:
beams gen_test_ioc my_tree.json > outfile.py

Then, edit outfile.py to set useful starting values and add logic if needed.
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


def main(*args, **kwargs):
    from beams.bin.gen_test_ioc_main import main
    main(*args, **kwargs)
