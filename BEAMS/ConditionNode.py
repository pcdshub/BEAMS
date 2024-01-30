import time
import py_trees
import atexit


class ConditionNode(py_trees.behaviour.Behaviour):
  def __init__(self, name, condition):
    super(ConditionNode, self).__init__(name)
    self.condition = condition  # condition to be evaluated
    self.logger.debug("%s.__init__()" % (self.__class__.__name__))


def main():
  pass


if __name__ == "__main__":
  main()
