import time
from pathlib import Path

import py_trees
from caproto.tests.conftest import run_example_ioc
from epics import caget

from beams.behavior_tree.CheckAndDo import CheckAndDo
from beams.tree_config import get_tree_from_path


def test_tree_obj_ser():
    fname = Path(__file__).parent / "artifacts" / "eggs.json"
    tg = get_tree_from_path(fname)

    assert isinstance(tg, py_trees.trees.BehaviourTree)
    assert isinstance(tg.root, CheckAndDo)


def test_tree_obj_execution(request):
    fname = Path(__file__).parent / "artifacts" / "eggs.json"
    tree = get_tree_from_path(fname)

    # start mock IOC # NOTE: assumes test is being run from top level of
    run_example_ioc(
        "beams.tests.mock_iocs.SelfTestIOC",
        request=request,
        pv_to_check="PERC:COMP",
    )

    tree.setup()
    while tree.root.status not in (
        py_trees.common.Status.SUCCESS,
        py_trees.common.Status.FAILURE,
    ):
        tree.tick()
        time.sleep(0.05)

    rel_val = caget("PERC:COMP")
    assert rel_val >= 100


def test_father_tree_execution(request):
    run_example_ioc(
        "beams.tests.mock_iocs.ImagerNaysh",
        request=request,
        pv_to_check="RET:INSERT",
    )

    fname = Path(__file__).parent / "artifacts" / "eggs2.json"
    tree = get_tree_from_path(fname)
    tree.setup()
    ct = 0
    while (
        tree.root.status
        not in (py_trees.common.Status.SUCCESS, py_trees.common.Status.FAILURE)
        and ct < 50
    ):
        ct += 1
        print((tree.root.status, tree.root.status, ct))
        tree.tick()
        time.sleep(0.05)

    check_insert = caget("RET:INSERT")

    assert check_insert == 1
