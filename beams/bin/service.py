"""
Start the beams service.

beams service
"""


import argparse
import logging

logger = logging.getLogger(__name__)


DESCRIPTION = __doc__


def build_arg_parser(argparser=None):
    if argparser is None:
        argparser = argparse.ArgumentParser()

    argparser.description = DESCRIPTION
    argparser.formatter_class = argparse.RawTextHelpFormatter


def main(*args, **kwargs):
    from beams.bin.service_main import main
    main(*args, **kwargs)
