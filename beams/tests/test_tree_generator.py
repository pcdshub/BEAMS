import time
from pathlib import Path

import py_trees
from caproto.tests.conftest import run_example_ioc
from epics import caget

from beams.tree_generator.TreeGenerator import TreeGenerator
from beams.tree_generator.TreeSerializer import (CheckAndDoNodeEntry,
                                                 CheckAndDoNodeTypeMode,
                                                 CheckEntry, DoEntry, TreeSpec)


def test_tree_obj_ser():
    fname = Path(__file__).parent / "artifacts" / "eggs.json"
    tg = TreeGenerator(fname, CheckAndDoNodeEntry)

    ce = CheckEntry(Pv="PERC:COMP", Thresh=100)
    de = DoEntry(Pv="PERC:COMP", Mode=CheckAndDoNodeTypeMode.INC, Value=10)
    eg = CheckAndDoNodeEntry(
        name="self_test",
        check_and_do_type=CheckAndDoNodeEntry.CheckAndDoNodeType.CHECKPV,
        check_entry=ce,
        do_entry=de,
    )

    assert tg.tree_spec == eg


def test_tree_obj_execution(request):
    fname = Path(__file__).parent / "artifacts" / "eggs.json"
    tg = TreeGenerator(fname, CheckAndDoNodeEntry)

    # start mock IOC # NOTE: assumes test is being run from top level of
    run_example_ioc(
        "beams.tests.mock_iocs.SelfTestIOC",
        request=request,
        pv_to_check="PERC:COMP",
    )

    tree = tg.get_tree_from_config()
    tree.setup_with_descendants()
    while (
        tree.status != py_trees.common.Status.SUCCESS
        and tree.status != py_trees.common.Status.FAILURE
    ):
        for n in tree.tick():
            print(f"ticking: {n}")
            time.sleep(0.05)
            print(f"status of tick: {n.status}")

    rel_val = caget("PERC:COMP")
    assert rel_val >= 100


def test_father_tree_execution(request):
    run_example_ioc(
        "beams.tests.mock_iocs.ImagerNaysh",
        request=request,
        pv_to_check="RET:INSERT",
    )

    fname = "beams/tests/artifacts/eggs2.json"
    tg = TreeGenerator(fname, TreeSpec)
    tree = tg.get_tree_from_config()

    ct = 0
    while (
        tree.root.status != py_trees.common.Status.SUCCESS
        and tree.root.status != py_trees.common.Status.FAILURE
        and ct < 50
    ):
        ct += 1
        print((tree.root.status, tree.root.status, ct))
        for n in tree.root.tick():
            print(f"ticking: {n}")
            time.sleep(0.05)
            print(f"status of tick: {n.status}")

    check_insert = caget("RET:INSERT")

    assert check_insert == 1
