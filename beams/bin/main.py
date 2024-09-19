"""
`beams` is the top-level command for accessing various subcommands.
"""

import argparse
import importlib
import logging

import beams
from beams.logging import setup_logging

DESCRIPTION = __doc__


COMMAND_TO_MODULE = {
    "run": "run",
}


def _try_import(module_name):
    return importlib.import_module(f".{module_name}", "beams.bin")


def _build_commands():
    global DESCRIPTION
    result = {}
    unavailable = []

    for command, module_name in sorted(COMMAND_TO_MODULE.items()):
        try:
            module = _try_import(module_name)
        except Exception as ex:
            unavailable.append((command, ex))
        else:
            result[module_name] = (module.build_arg_parser, module.main)
            DESCRIPTION += f'\n    $ beams {command} --help'

    if unavailable:
        DESCRIPTION += '\n\n'

        for command, ex in unavailable:
            DESCRIPTION += (
                f'\nWARNING: "beams {command}" is unavailable due to:'
                f'\n\t{ex.__class__.__name__}: {ex}'
            )

    return result


COMMANDS = _build_commands()


def main():
    top_parser = argparse.ArgumentParser(
        prog='beams',
        description=DESCRIPTION,
        formatter_class=argparse.RawTextHelpFormatter
    )

    top_parser.add_argument(
        '--version', '-V',
        action='version',
        version=beams.__version__,
        help="Show the beams version number and exit."
    )

    top_parser.add_argument(
        '--log', '-l', dest='log_level',
        default='INFO',
        type=str,
        help='Python logging level (e.g. DEBUG, INFO, WARNING)'
    )

    subparsers = top_parser.add_subparsers(help='Possible subcommands')
    for command_name, (build_func, main) in COMMANDS.items():
        sub = subparsers.add_parser(command_name)
        build_func(sub)
        sub.set_defaults(func=main)

    args = top_parser.parse_args()
    kwargs = vars(args)
    log_level = kwargs.pop('log_level')

    setup_logging(log_level)
    logger = logging.getLogger("beams")

    if hasattr(args, 'func'):
        func = kwargs.pop('func')
        logger.debug('%s(**%r)', func.__name__, kwargs)
        func(**kwargs)
    else:
        top_parser.print_help()


if __name__ == '__main__':
    main()
