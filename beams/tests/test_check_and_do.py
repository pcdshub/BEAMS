import time
from multiprocessing import Value

import py_trees

from beams.behavior_tree import ActionNode, CheckAndDo, ConditionNode


class TestTask:
  def test_check_and_do(self, capsys):
    percentage_complete = Value('i', 0)

    def thisjob(comp_condition, volatile_status, **kwargs) -> None:
      # TODO: grabbing intended keyword argument. Josh's less than pythonic mechanism for closures
      volatile_status.set_value(py_trees.common.Status.RUNNING)
      percentage_complete = kwargs["percentage_complete"]
      while not comp_condition(percentage_complete.value):
        py_trees.console.logdebug(f"yuh {percentage_complete.value}, {volatile_status.get_value()}")
        percentage_complete.value += 10
        if percentage_complete.value == 100:
          volatile_status.set_value(py_trees.common.Status.SUCCESS)
        time.sleep(0.001)

    py_trees.logging.level = py_trees.logging.Level.DEBUG
    comp_cond = lambda x: x == 100
    action = ActionNode.ActionNode("action", thisjob, comp_cond, percentage_complete=percentage_complete)

    checky = lambda x: x.value == 100
    check = ConditionNode.ConditionNode("check", checky, percentage_complete)

    candd = CheckAndDo.CheckAndDo("yuhh", check, action)
    candd.setup_with_descendants()

    while (
        candd.status != py_trees.common.Status.SUCCESS
        and candd.status != py_trees.common.Status.FAILURE
    ):
      for i in candd.tick():
        time.sleep(.01)

    assert percentage_complete.value == 100
