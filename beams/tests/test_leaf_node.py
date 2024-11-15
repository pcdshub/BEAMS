import logging
import time
from multiprocessing import Value
from typing import Callable

from py_trees.common import Status

from beams.behavior_tree.action_node import ActionNode, wrapped_action_work
from beams.behavior_tree.condition_node import ConditionNode

logger = logging.getLogger(__name__)


def test_action_node(bt_cleaner):
    # For test
    percentage_complete = Value("i", 0)

    @wrapped_action_work(loop_period_sec=0.001)
    def work_func(comp_condition: Callable) -> Status:
        percentage_complete.value += 10
        if comp_condition():
            return Status.SUCCESS
        logger.debug(f"pct complete -> {percentage_complete.value}")
        return Status.RUNNING

    def comp_cond():
        return percentage_complete.value >= 100

    action = ActionNode(name="action", work_func=work_func,
                        completion_condition=comp_cond)
    bt_cleaner.register(action)
    action.setup()
    for _ in range(20):
        time.sleep(0.01)
        action.tick_once()
    assert percentage_complete.value == 100


def test_action_node_timeout(bt_cleaner):
    # For test
    percentage_complete = Value("i", 0)

    @wrapped_action_work(loop_period_sec=0.001, work_function_timeout_period_sec=.002)
    def work_func(comp_condition: Callable) -> Status:
        percentage_complete.value += 10
        if comp_condition():
            return Status.SUCCESS
        logger.debug(f"pct complete -> {percentage_complete.value}")
        return Status.RUNNING

    def comp_cond():
        return percentage_complete.value >= 100

    action = ActionNode(name="action", work_func=work_func,
                        completion_condition=comp_cond)
    bt_cleaner.register(action)
    action.setup()

    while action.status not in (
        Status.SUCCESS,
        Status.FAILURE,
    ):
        time.sleep(0.01)
        action.tick_once()
    assert action.status == Status.FAILURE
    assert percentage_complete.value != 100


def test_condition_node(bt_cleaner):
    def condition_fn():
        return True

    con = ConditionNode("con", condition_fn)
    bt_cleaner.register(con)
    con.setup()
    assert con.status == Status.INVALID
    for _ in range(3):
        con.tick_once()
        time.sleep(0.01)

    assert con.status == Status.SUCCESS


def test_condition_node_with_arg(bt_cleaner):
    def check(val):
        return val

    value = False
    con = ConditionNode("con", check, value)
    bt_cleaner.register(con)
    con.setup()
    assert con.status == Status.INVALID
    for _ in range(3):
        con.tick_once()
        time.sleep(0.01)

    assert con.status == Status.FAILURE
