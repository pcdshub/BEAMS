import time

import py_trees
from caproto.tests.conftest import run_example_ioc

from beams.tree_config.utility_trees.reset_ioc import ResetIOCItem


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
            time.sleep(1)
