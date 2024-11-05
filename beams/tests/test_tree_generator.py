import time
from pathlib import Path

import py_trees
from caproto.tests.conftest import run_example_ioc
from epics import caget, caput

from beams.behavior_tree.CheckAndDo import CheckAndDo
from beams.tree_config.tree_config import (CheckAndDoItem, get_tree_from_path,
                                           save_tree_item_to_path)


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
        for n in tree.root.tick():
            print(n)
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
        for n in tree.root.tick():
            ct += 1
            print(n)
            print((tree.root.status, tree.root.status, ct))
            time.sleep(0.05)

    check_insert = caget("RET:INSERT")

    assert check_insert == 1


def test_save_tree_item_round_trip(tmp_path: Path):
    filepath = tmp_path / "temp_egg.json"
    item = CheckAndDoItem(name="test_save_tree_item_round_trip")
    save_tree_item_to_path(path=filepath, root=item)
    loaded_tree = get_tree_from_path(path=filepath)
    assert isinstance(loaded_tree.root, CheckAndDo)
    assert loaded_tree.root.name == item.name


def test_stop_hitting_yourself(request):
    run_example_ioc(
        "beams.tests.mock_iocs.IM2L0",
        request=request,
        pv_to_check="IM2L0:XTES:MMS:STATE:GET_RBV",
    )

    fname = Path(__file__).parent / "artifacts" / "im2l0_test.json"
    tree = get_tree_from_path(fname)
    tree.setup()
    ct = 0
    while (
        tree.root.status
        not in (py_trees.common.Status.SUCCESS, py_trees.common.Status.FAILURE)
        and ct < 50
    ):
        for n in tree.root.tick():
            ct += 1
            print(n)
            print((tree.root.status, tree.root.status, ct))
            time.sleep(0.05)

    # Hit myself
    caput("IM2L0:XTES:CLZ.RBV", 75)

    ct = 0
    while (
        ct == 0  # simulate a constantly monitoring tree
        or
        tree.root.status
        not in (py_trees.common.Status.SUCCESS, py_trees.common.Status.FAILURE)
        and ct < 50
    ):
        for n in tree.root.tick():
            ct += 1
            print(n)
            print((tree.root.status, tree.root.status, ct))
            time.sleep(0.05)

    check_insert = caget("IM2L0:XTES:MMS:STATE:GET_RBV", as_string=True)
    check_zoom_motor = caget("IM2L0:XTES:CLZ.RBV")
    check_focus_motor = caget("IM2L0:XTES:CLF.RBV")

    assert check_insert == "OUT"
    assert check_zoom_motor == 25
    assert check_focus_motor == 50
