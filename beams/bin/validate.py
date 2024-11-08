"""
`beams validate` can be used to validate json file schemas.
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
    from beams.bin.validate_main import main
    return main(*args, **kwargs)
