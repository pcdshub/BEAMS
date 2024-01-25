import time
import py_trees
import atexit
import multiprocessing
import multiprocessing.connection


class ActionNode(py_trees.behaviour.Behaviour):
  def __init__(self, name, work_func):
    super(ActionNode, self).__init__(name)
    self.work_func = work_func
    self.logger.debug("%s.__init__()" % (self.__class__.__name__))

  def setup(self, **kwargs: int) -> None:
    """Kickstart the separate process this behaviour will work with.
    Ordinarily this process will be already running. In this case,
    setup is usually just responsible for verifying it exists.
    """
    self.logger.debug(
        "%s.setup()->connections to an external process" % (self.__class__.__name__)
    )
    self.parent_connection, self.child_connection = multiprocessing.Pipe()
    self.planning = multiprocessing.Process(
        target=self.work_func, args=(self.child_connection,)
    )
    atexit.register(self.terminate, py_trees.common.Status.FAILURE)
    self.planning.start()

  def initialise(self) -> None:
    """Reset a counter variable."""
    self.logger.debug(
        "%s.initialise()->sending new goal" % (self.__class__.__name__)
    )
    self.parent_connection.send(["new goal"])
    self.percentage_completion = 0

  def update(self) -> py_trees.common.Status:
    """Increment the counter, monitor and decide on a new status."""
    new_status = py_trees.common.Status.RUNNING
    if self.parent_connection.poll():
        self.percentage_completion = self.parent_connection.recv().pop()
        if self.percentage_completion == 100:
            new_status = py_trees.common.Status.SUCCESS
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
    else:
        self.feedback_message = "{0}%".format(self.percentage_completion)
        self.logger.debug(
            "%s.update()[%s][%s]"
            % (self.__class__.__name__, self.status, self.feedback_message)
        )
    return new_status

  def terminate(self, new_status: py_trees.common.Status) -> None:
      """Nothing to clean up in this example."""
      self.planning.terminate()
      self.logger.debug(
          "%s.terminate()[%s->%s]"
          % (self.__class__.__name__, self.status, new_status)
      )


def thisjob(connection: multiprocessing.connection.Connection) -> None:
  idle = True
  percentage_complete = 0
  try:
    while True:
      if connection.poll():
        connection.recv()  # discarding
        percentage_complete = 0
        idle = False
      if not idle:
        percentage_complete += 10
        connection.send([percentage_complete])
        if percentage_complete == 100:
          idle = True
      time.sleep(0.5)
  except KeyboardInterrupt:
    pass


def main():
  py_trees.logging.level = py_trees.logging.Level.DEBUG
  action = ActionNode("action", thisjob)
  action.setup()
  for i in range(20):
    action.tick_once()
    time.sleep(0.5)


if __name__ == '__main__':
  main()
