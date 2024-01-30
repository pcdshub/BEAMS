import time
import py_trees


class ConditionNode(py_trees.behaviour.Behaviour):
  def __init__(self, name, condition):
    super(ConditionNode, self).__init__(name)
    self.condition = condition  # condition to be evaluated
    self.logger.debug("%s.__init__()" % (self.__class__.__name__))

  def update(self):
    state = self.condition()
    # we take true to mean success
    if state is True:
      ret = py_trees.common.Status.SUCCESS
    else:
      ret = py_trees.common.Status.FAILURE
    self.logger.debug(py_trees.console.cyan + f"Ticking: {self.name} results in {ret}")
    return ret


# For test
def main():
  yuh = lambda: True
  connie = ConditionNode("con", yuh)
  py_trees.logging.level = py_trees.logging.Level.DEBUG
  connie.setup()
  for i in range(3):
    connie.tick_once()
    time.sleep(1)


if __name__ == "__main__":
  main()
