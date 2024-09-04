import time
from typing import Callable, Any
from multiprocessing import Value

import py_trees

from beams.behavior_tree.ActionNode import ActionNode
from beams.behavior_tree.ConditionNode import ConditionNode
from beams.behavior_tree.VolatileStatus import VolatileStatus


class TestTask:
    def test_action_node(self, capsys):
        py_trees.logging.level = py_trees.logging.Level.DEBUG
        # For test
        percentage_complete = Value("i", 0)

        def thisjob(myself, 
                    comp_condition: Callable[[Any], None], 
                    volatile_status: VolatileStatus, 
                    *args) -> None:
            volatile_status.set_value(py_trees.common.Status.RUNNING)
            while not comp_condition(percentage_complete.value):
                py_trees.console.logdebug(f"yuh {percentage_complete.value}, {volatile_status.get_value()}")
                percentage_complete.value += 10
                if percentage_complete.value == 100:
                  volatile_status.set_value(py_trees.common.Status.SUCCESS)
                time.sleep(0.001)

        py_trees.logging.level = py_trees.logging.Level.DEBUG
        comp_cond = lambda x: x == 100
        action = ActionNode(name="action", 
                            work_func=thisjob, 
                            completion_condition=comp_cond)
        action.setup()
        for i in range(20):
          time.sleep(0.01)
          action.tick_once()

        assert percentage_complete.value == 100

    def test_condition_node(self):
        yuh = lambda: True
        con = ConditionNode("con", yuh)
        py_trees.logging.level = py_trees.logging.Level.DEBUG
        con.setup()
        for i in range(3):
            con.tick_once()
            time.sleep(0.01)

    def test_condition_node_with_arg(self):
        def check(val):
            True if val is True else False

        value = False
        con = ConditionNode("con", check, value)
        py_trees.logging.level = py_trees.logging.Level.DEBUG
        con.setup()
        for i in range(3):
            con.tick_once()
            time.sleep(0.01)
