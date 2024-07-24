from multiprocessing import Value
import time
import py_trees
from beams.behavior_tree import ActionNode, ConditionNode, CheckAndDo


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
    candd.setup()

    for i in range(1, 10):
      time.sleep(.01)
      candd.root.tick_once()

    assert percentage_complete.value == 100
