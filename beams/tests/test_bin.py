import functools
import itertools
import logging
from pathlib import Path

import pytest

from beams.bin.main import main
from beams.tests.conftest import cli_args, restore_logging

logger = logging.getLogger(__name__)

SUBCOMMANDS = ["", "run",]


def arg_variants(variants: tuple[tuple[tuple[str]]]):
    """
    Collapse argument variants into all possible combinations.
    """
    for idx, arg_set in enumerate(itertools.product(*variants), 1):
        item = functools.reduce(
            lambda x, y: x+y,
            arg_set,
        )
        summary = f"args{idx}_" + ",".join(item)
        yield pytest.param(item, id=summary)


@pytest.mark.parametrize("subcommand", SUBCOMMANDS)
def test_main_normal(subcommand: str):
    args = ["beams", "--help"]
    if subcommand:
        args.insert(1, subcommand)
    with pytest.raises(SystemExit), cli_args(args), restore_logging():
        main()


def test_main_noargs():
    with cli_args(["beams"]), restore_logging():
        main()


RUN_ARGS = (
    (("-t", "2"), ("--tick-count", "2"), ()),
    (("--show-node-status",), ()),
    (("--show-tree",), ()),
    (("--show-blackboard",), ()),
)


@pytest.mark.parametrize("added_args", tuple(arg_variants(RUN_ARGS)))
def test_run(added_args: tuple[str]):
    test_cfg = Path(__file__).parent / "artifacts" / "eternal_guard.json"
    args = ["beams", "run", str(test_cfg), "-d", "0"]
    args.extend(added_args)
    print(args)
    with cli_args(args), restore_logging():
        main()
