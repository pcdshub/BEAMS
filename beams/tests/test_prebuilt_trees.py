import time

import py_trees
from caproto.tests.conftest import run_example_ioc

from beams.behavior_tree.condition_node import AckConditionNode
from beams.tree_config.condition import AcknowledgeConditionItem
from beams.tree_config.prebuilt.reset_ioc import ResetIOCItem
from beams.tree_config.prebuilt.wait_for_ack import WaitForAckNodeItem


def test_sys_reset(request, bt_cleaner):
    reset_ioc_tree = ResetIOCItem(
                        ioc_prefix="SysResetTest").get_tree()

    bt_cleaner.register(reset_ioc_tree)

    # start mock IOC # NOTE: assumes test is being run from top level of
    run_example_ioc(
        "beams.tests.mock_iocs.SysResetIOC",
        request=request,
        pv_to_check="SysResetTest:HEARTBEAT",
    )

    reset_ioc_tree.setup_with_descendants()
    while reset_ioc_tree.status not in (
        py_trees.common.Status.SUCCESS,
        py_trees.common.Status.FAILURE,
    ):
        for n in reset_ioc_tree.tick():
            print(n)
            time.sleep(0.01)

    assert reset_ioc_tree.status == py_trees.common.Status.SUCCESS


def test_acknowledge(bt_cleaner):
    ack_cond_node = AcknowledgeConditionItem(
        name="test ack node",
        permisible_user_list=["robert", "zach"]
    )

    root = ack_cond_node.get_tree()

    root.acknowledge_node("josh")

    i = 0
    while (root.status != py_trees.common.Status.SUCCESS and i < 2):
        for n in root.tick():
            i += 1
            print(n)

    assert (root.status == py_trees.common.Status.FAILURE)

    root.acknowledge_node("robert")
    i = 0
    while (root.status != py_trees.common.Status.SUCCESS and i < 2):
        for n in root.tick():
            i += 1
            print(n)

    assert (root.status == py_trees.common.Status.SUCCESS)


def test_wait_and_acknowledge(bt_cleaner):
    ack_cond_item = ack_cond_item = AcknowledgeConditionItem(
        name="test_ack_node",
        permisible_user_list=["silke", "barry"]
    )
    egg = WaitForAckNodeItem(ack_cond_item=ack_cond_item, wait_time_out=1)
    root = egg.get_tree()
    bt_cleaner.register(root)

    root.setup_with_descendants()

    i = 0
    while root.status not in (
        py_trees.common.Status.SUCCESS,
        py_trees.common.Status.FAILURE,
    ) and i < 5:
        i += 1
        print(i)
        for n in root.tick():
            time.sleep(0.1)
        print(f"ROOT STATUS: {root.status}")

    assert root.status == py_trees.common.Status.FAILURE

    # this is the same mechanism the service will use to signal
    node_name = "test_ack_node"
    node_to_ack = None
    for i in root.iterate():
        if (i.name == node_name and isinstance(i, AckConditionNode)):
            node_to_ack = i

    assert node_to_ack is not None
    if node_to_ack is not None:
        node_to_ack.acknowledge_node("silke")
        assert node_to_ack.check_ack()
