import logging
import time
from multiprocessing import Value
from typing import Callable

from py_trees.common import Status

from beams.behavior_tree.ActionNode import ActionNode
from beams.behavior_tree.ConditionNode import ConditionNode

logger = logging.getLogger(__name__)


def test_action_node():
    # For test
    percentage_complete = Value("i", 0)

    def work_func(comp_condition: Callable) -> Status:
        percentage_complete.value += 10
        if comp_condition():
            return Status.SUCCESS
        logger.debug(f"pct complete -> {percentage_complete.value}")
        time.sleep(0.001)
        return Status.RUNNING

    def comp_cond():
        return percentage_complete.value >= 100

    action = ActionNode(name="action", work_func=work_func,
                        completion_condition=comp_cond)
    action.setup()
    for _ in range(20):
        time.sleep(0.01)
        action.tick_once()
    assert percentage_complete.value == 100


def test_condition_node():
    def condition_fn():
        return True

    con = ConditionNode("con", condition_fn)
    con.setup()
    assert con.status == Status.INVALID
    for _ in range(3):
        con.tick_once()
        time.sleep(0.01)

    assert con.status == Status.SUCCESS


def test_condition_node_with_arg():
    def check(val):
        return val

    value = False
    con = ConditionNode("con", check, value)
    con.setup()
    assert con.status == Status.INVALID
    for _ in range(3):
        con.tick_once()
        time.sleep(0.01)

    assert con.status == Status.FAILURE
