import functools
import itertools
import logging
import subprocess
from pathlib import Path

import caproto.server
import caproto.server.server
import pytest
from caproto import ChannelType
from caproto.server import PVGroup, pvproperty
from caproto.tests.conftest import run_example_ioc

from beams.bin.gen_test_ioc_main import collect_pv_info
from beams.bin.main import main
from beams.tests.conftest import cli_args, restore_logging
from beams.tree_config import save_tree_item_to_path
from beams.tree_config.value import EPICSValue
from beams.tree_config.composite import SequenceItem
from beams.tree_config.condition import BinaryConditionItem

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


def test_collect_pvinfo(
    request: pytest.FixtureRequest,
):
    run_example_ioc(
        "beams.tests.mock_iocs.various_types_ioc",
        request=request,
        pv_to_check="VAR:TYPES:INT",
    )
    pv_info = collect_pv_info([
        "VAR:TYPES:INT",
        "VAR:TYPES:FLOAT",
        "VAR:TYPES:STRING",
        "VAR:TYPES:ENUM",
    ])
    for info in pv_info:
        if info.pvname == "VAR:TYPES:INT":
            assert info.python_name == "var_types_int"
            assert info.dtype == "INT"
            assert info.value == 3
        elif info.pvname == "VAR:TYPES:FLOAT":
            assert info.python_name == "var_types_float"
            assert info.dtype == "FLOAT"
            assert info.value == pytest.approx(3.14)
            assert info.precision == 3
        elif info.pvname == "VAR:TYPES:STRING":
            assert info.python_name == "var_types_string"
            assert info.dtype == "STRING"
            assert info.value == "pi"
        elif info.pvname == "VAR:TYPES:ENUM":
            assert info.python_name == "var_types_enum"
            assert info.dtype == "ENUM"
            assert info.value == 0
            assert info.enum_strings == ["apple", "pumpkin", "shepherd's"]
        else:
            raise RuntimeError(f"Unexpected pvname {info.pvname}")


def test_gen_test_ioc_online(
    request: pytest.FixtureRequest,
    capsys: pytest.CaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    run_example_ioc(
        "beams.tests.mock_iocs.various_types_ioc",
        request=request,
        pv_to_check="VAR:TYPES:INT",
    )
    check_int = BinaryConditionItem(left_value=EPICSValue("VAR:TYPES:INT"))
    check_float = BinaryConditionItem(left_value=EPICSValue("VAR:TYPES:FLOAT"))
    check_string = BinaryConditionItem(left_value=EPICSValue("VAR:TYPES:STRING"))
    check_enum = BinaryConditionItem(left_value=EPICSValue("VAR:TYPES:ENUM"))
    seq = SequenceItem(children=[check_int, check_float, check_string, check_enum])
    temp_file = str(tmp_path / "temp.json")
    save_tree_item_to_path(path=temp_file, root=seq)
    args = ["beams", "gen_test_ioc", temp_file]
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
    assert isinstance(BTSimIOC.var_types_int, pvproperty)
    assert isinstance(BTSimIOC.var_types_float, pvproperty)
    assert isinstance(BTSimIOC.var_types_string, pvproperty)
    assert isinstance(BTSimIOC.var_types_enum, pvproperty)
    assert BTSimIOC.var_types_int.pvspec.name == "VAR:TYPES:INT"
    assert BTSimIOC.var_types_float.pvspec.name == "VAR:TYPES:FLOAT"
    assert BTSimIOC.var_types_string.pvspec.name == "VAR:TYPES:STRING"
    assert BTSimIOC.var_types_enum.pvspec.name == "VAR:TYPES:ENUM"
    assert BTSimIOC.var_types_int.pvspec.dtype == ChannelType.INT
    assert BTSimIOC.var_types_float.pvspec.dtype == ChannelType.FLOAT
    assert BTSimIOC.var_types_string.pvspec.dtype == ChannelType.STRING
    assert BTSimIOC.var_types_enum.pvspec.dtype == ChannelType.ENUM

    ioc = BTSimIOC(prefix="")
    assert "VAR:TYPES:INT" in ioc.pvdb
    assert "VAR:TYPES:FLOAT" in ioc.pvdb
    assert "VAR:TYPES:STRING" in ioc.pvdb
    assert "VAR:TYPES:ENUM" in ioc.pvdb

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
