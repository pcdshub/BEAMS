import functools
import itertools
import logging
import subprocess
from pathlib import Path

import caproto.server
import caproto.server.server
import pytest
from caproto.server import PVGroup, pvproperty

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
    (("--hide-node-status",), ()),
    (("--hide-tree",), ()),
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


def test_gen_test_ioc_offline(capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch):
    test_cfg = Path(__file__).parent / "artifacts" / "eggs.json"
    args = ["beams", "gen_test_ioc", "--offline", str(test_cfg)]
    with cli_args(args), restore_logging():
        main()
    result = capsys.readouterr()
    code = result.out
    assert isinstance(code, str)
    logger.debug(f"Generated file:\n{code}")
    inner_globals = {}
    run_called = 0

    def mock_run(*args, **kwargs):
        nonlocal run_called
        run_called += 1

    # Paranoia: stop run from running if the generated file tries to run
    monkeypatch.setattr(caproto.server, "run", mock_run)
    monkeypatch.setattr(caproto.server.server, "run", mock_run)
    exec(code, inner_globals)
    BTSimIOC = inner_globals["BTSimIOC"]
    assert issubclass(BTSimIOC, PVGroup)
    assert isinstance(BTSimIOC.perc_comp, pvproperty)
    assert BTSimIOC.perc_comp.pvspec.name == "PERC:COMP"

    ioc = BTSimIOC(prefix="TST:")
    assert "TST:PERC:COMP" in ioc.pvdb

    # We essentially did an import, no run should have happened
    assert not run_called


artifact_validation_codes = [
    # Standard test eggs should work
    ("eggs.json", 0),
    ("eggs2.json", 0),
    ("eternal_guard.json", 0),
    ("im2l0_test.json", 0),
    # File not found error
    ("no_egg", 2),
    # Not even json, just empty!
    ("bad_egg1.txt", 2),
    # A yaml file
    ("bad_egg2.yaml", 2),
    # An empty dict
    ("bad_egg3.json", 1),
    # Missing root
    ("bad_egg4.json", 1),
]


@pytest.mark.parametrize("artifact, return_code", artifact_validation_codes)
def test_validate_artifacts_subproc(artifact: str, return_code: int):
    test_cfg = (Path(__file__).parent / "artifacts" / artifact).resolve()
    cproc = subprocess.run(["python3", "-m", "beams", "validate", str(test_cfg)], capture_output=True, universal_newlines=True)
    assert cproc.returncode == return_code, cproc.stdout


@pytest.mark.parametrize("artifact, return_code", artifact_validation_codes)
def test_validate_artifacts_inproc(artifact: str, return_code: int):
    test_cfg = Path(__file__).parent / "artifacts" / artifact
    args = ["beams", "validate", str(test_cfg)]
    with cli_args(args), restore_logging():
        assert main() == return_code
