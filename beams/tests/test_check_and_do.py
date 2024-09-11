import logging
import time
from multiprocessing import Value

import py_trees
from py_trees.common import Status

from beams.behavior_tree import ActionNode, CheckAndDo, ConditionNode

logger = logging.getLogger(__name__)


def test_check_and_do():
    percentage_complete = Value("i", 0)

    def thisjob(comp_condition) -> None:
        logger.debug(f"PERC COMP {percentage_complete.value}")
        percentage_complete.value += 10
        if comp_condition():
            return Status.SUCCESS
        time.sleep(0.001)
        return Status.RUNNING

    def comp_cond():
        return percentage_complete.value >= 100

    action = ActionNode.ActionNode(
        name="action",
        work_func=thisjob,
        completion_condition=comp_cond
    )

    def check_fn(x: Value):
        return x.value == 100

    check = ConditionNode.ConditionNode("check", check_fn, percentage_complete)

    candd = CheckAndDo.CheckAndDo("yuhh", check, action)
    candd.setup_with_descendants()

    while (
        candd.status != py_trees.common.Status.SUCCESS
        and candd.status != py_trees.common.Status.FAILURE
    ):
        for _ in candd.tick():
            time.sleep(0.01)

    assert percentage_complete.value == 100
