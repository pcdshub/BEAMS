import time
from math import isclose
from pathlib import Path

import py_trees
from caproto.tests.conftest import run_example_ioc
from epics import caget, caput
from py_trees.common import Status

from beams.behavior_tree.check_and_do import CheckAndDo
from beams.tests.conftest import wait_until
from beams.tree_config import get_tree_from_path, save_tree_item_to_path
from beams.tree_config.idiom import CheckAndDoItem


def test_tree_obj_ser():
    fname = Path(__file__).parent / "artifacts" / "eggs.json"
    tg = get_tree_from_path(fname)

    assert isinstance(tg, py_trees.trees.BehaviourTree)
    assert isinstance(tg.root, CheckAndDo)


def test_increment_tree(request, bt_cleaner):
    """Tests a tree that increments a PV until it is > 100"""
    fname = Path(__file__).parent / "artifacts" / "eggs.json"
    tree = get_tree_from_path(fname)
    bt_cleaner.register(tree)

    # start mock IOC # NOTE: assumes test is being run from top level of
    run_example_ioc(
        "beams.tests.mock_iocs.SelfTestIOC",
        request=request,
        pv_to_check="PERC:COMP",
    )
    # verify connections
    wait_until(lambda: caget("PERC:COMP") == 1, timeout=10)

    ct = 0
    tree.setup()
    while tree.root.status not in (Status.SUCCESS, Status.FAILURE):
        ct += 1
        for n in tree.root.tick():
            print(n, n.status, ct)
            time.sleep(0.05)

    rel_val = caget("PERC:COMP")
    assert (rel_val is not None) and (rel_val >= 100)


def test_reticle_find_insert_tree(request, bt_cleaner):
    """Tests a tree that first sets RET:FOUND -> 1, then RET:INSERT -> 1"""
    run_example_ioc(
        "beams.tests.mock_iocs.ImagerNaysh",
        request=request,
        pv_to_check="RET:INSERT",
    )

    fname = Path(__file__).parent / "artifacts" / "eggs2.json"
    tree = get_tree_from_path(fname)
    bt_cleaner.register(tree)

    # verify connections
    wait_until(lambda: caget("RET:FOUND") == 0, timeout=10)
    wait_until(lambda: caget("RET:INSERT") == 0, timeout=10)

    tree.setup()
    ct = 0
    while (
        tree.root.status not in (Status.SUCCESS, Status.FAILURE)
        and ct < 50
    ):
        ct += 1
        for n in tree.root.tick():
            print((n, tree.root.status, ct))
            time.sleep(0.05)

            if (
                caget("RET:FOUND") == 1
                and caget("RET:INSERT") == 1
                and ct < 49
            ):
                print("Condition fulfilled, stopping tick loop early")
                # allow one more tick to update statuses
                ct = 49

    assert caget("RET:FOUND") == 1
    assert caget("RET:INSERT") == 1
    assert tree.root.status == Status.SUCCESS


def test_save_tree_item_round_trip(tmp_path: Path):
    filepath = tmp_path / "temp_egg.json"
    item = CheckAndDoItem(name="test_save_tree_item_round_trip")
    save_tree_item_to_path(path=filepath, root=item)
    loaded_tree = get_tree_from_path(path=filepath)
    assert isinstance(loaded_tree.root, CheckAndDo)
    assert loaded_tree.root.name == item.name


def test_stop_hitting_yourself(request, bt_cleaner):
    """Tests a tree that reactively resets a PV"""
    run_example_ioc(
        "beams.tests.mock_iocs.IM2L0",
        request=request,
        pv_to_check="IM2L0:XTES:MMS:STATE:GET_RBV",
    )

    fname = Path(__file__).parent / "artifacts" / "im2l0_test.json"
    tree = get_tree_from_path(fname)
    bt_cleaner.register(tree)

    wait_until(
        lambda: caget("IM2L0:XTES:MMS:STATE:GET_RBV", as_string=True) == "UNKNOWN",
        timeout=10
    )
    wait_until(lambda: caget("IM2L0:XTES:CLZ.RBV") == 0, timeout=10)
    wait_until(lambda: caget("IM2L0:XTES:CLF.RBV") == 0, timeout=10)

    tree.setup()
    ct = 0
    while (
        tree.root.status not in (Status.SUCCESS, Status.FAILURE)
        and ct < 50
    ):
        ct += 1
        for n in tree.root.tick():
            print(n, tree.root.status, ct)
            time.sleep(0.05)

    # Hit myself
    caput("IM2L0:XTES:CLZ.RBV", 75)

    ct = 0
    while (
        ct == 0  # simulate a constantly monitoring tree
        or tree.root.status not in (Status.SUCCESS, Status.FAILURE)
        and ct < 50
    ):
        ct += 1
        for n in tree.root.tick():
            print(n, tree.root.status, tree.root.status, ct)
            time.sleep(0.05)

    check_insert = caget("IM2L0:XTES:MMS:STATE:GET_RBV", as_string=True)
    check_zoom_motor = caget("IM2L0:XTES:CLZ.RBV")
    check_focus_motor = caget("IM2L0:XTES:CLF.RBV")

    assert check_insert == "OUT"
    assert check_zoom_motor is not None
    assert isclose(25, check_zoom_motor, rel_tol=0.2)
    assert check_focus_motor == 50
