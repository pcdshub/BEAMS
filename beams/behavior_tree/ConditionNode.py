import py_trees


class ConditionNode(py_trees.behaviour.Behaviour):
  def __init__(self, name, condition, *args):
    super(ConditionNode, self).__init__(name)
    self.condition = condition  # condition to be evaluated
    self.logger.debug("%s.__init__()" % (self.__class__.__name__))
    self.condition_args = args

  def update(self):
    state = self.condition(*self.condition_args)
    # we take true to mean success
    if state is True:
      ret = py_trees.common.Status.SUCCESS
    else:
      ret = py_trees.common.Status.FAILURE
    self.logger.debug(py_trees.console.cyan + f"Ticking: {self.name} results in {ret}")
    return ret
