import time
import py_trees
import atexit
import multiprocessing
from VolatileStatus import VolatileStatus


class ActionNode(py_trees.behaviour.Behaviour):
  def __init__(self, name, work_func, completion_condition):  # TODO: can add failure condition argument...
    super(ActionNode, self).__init__(name)
    self.work_func = work_func
    self.comp_condition = completion_condition
    print(type(self.status))
    self.__volatile_status__ = VolatileStatus(self.status)
    self.logger.debug("%s.__init__()" % (self.__class__.__name__))

  def setup(self, **kwargs: int) -> None:
    """Kickstart the separate process this behaviour will work with.
    Ordinarily this process will be already running. In this case,
    setup is usually just responsible for verifying it exists.
    """
    self.logger.debug(
        "%s.setup()->connections to an external process" % (self.__class__.__name__)
    )
    self.work_proc = multiprocessing.Process(
        target=self.work_func, args=(self.comp_condition, self.__volatile_status__)
    )
    atexit.register(self.terminate, py_trees.common.Status.FAILURE)
    print("Regardsless this should run")
    self.work_proc.start()

  def initialise(self) -> None:
    """ From docs the expected behavior is that status after initialize is running
    """
    current_status = self.__volatile_status__.get_value()
    if current_status == py_trees.common.Status.INVALID:
      self.__volatile_status__.set_value(py_trees.common.Status.RUNNING)

  def update(self) -> py_trees.common.Status:
    """Increment the counter, monitor and decide on a new status."""
    new_status = self.__volatile_status__.get_value()

    if new_status == py_trees.common.Status.SUCCESS:
        self.feedback_message = "Processing finished"
        self.logger.debug(
            "%s.update()[%s->%s][%s]"
            % (
                self.__class__.__name__,
                self.status,
                new_status,
                self.feedback_message,
            )
        )
    return new_status

  def terminate(self, new_status: py_trees.common.Status) -> None:
      """Nothing to clean up in this example."""
      if self.work_proc.is_alive():
        self.work_proc.terminate()
        self.logger.debug(
            py_trees.console.red + "%s.terminate()[%s->%s]"
            % (self.__class__.__name__, self.status, new_status)
        )


def thisjob(comp_condition, volatile_status) -> None:
  # initial setup
  percentage_complete = 0
  print("THIS SHOULD GO")
  try:
    while not comp_condition(percentage_complete):
      py_trees.console.logdebug(f"yuh {percentage_complete}, {volatile_status.get_value()}")
      percentage_complete += 10
      if percentage_complete == 100:
        volatile_status.set_value(py_trees.common.Status.SUCCESS)
      time.sleep(0.5)
  except KeyboardInterrupt:
    pass


def main():
  py_trees.logging.level = py_trees.logging.Level.DEBUG
  comp_cond = lambda x: x == 100
  action = ActionNode("action", thisjob, comp_cond)
  action.setup()
  for i in range(20):
    action.tick_once()
    time.sleep(0.5)


if __name__ == '__main__':
  main()
