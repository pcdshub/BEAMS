import py_trees
import atexit
from multiprocessing import Process, Event, Lock
from beams.behavior_tree.VolatileStatus import VolatileStatus
import os
import time


class ActionNode(py_trees.behaviour.Behaviour):
  def __init__(self, 
               name, 
               work_func, 
               completion_condition, 
               work_gate=Event(), 
               work_lock=Lock(),
               **kwargs):  # TODO: can add failure condition argument...
    super(ActionNode, self).__init__(name)
    self.work_func = work_func
    self.comp_condition = completion_condition
    # print(type(self.status))
    self.__volatile_status__ = VolatileStatus(self.status)
    self.additional_args = kwargs
    self.logger.debug("%s.__init__()" % (self.__class__.__name__))

    self.work_gate = work_gate
    self.lock = work_lock

  def setup(self, **kwargs: int) -> None:
    """Kickstart the separate process this behaviour will work with.
    Ordinarily this process will be already running. In this case,
    setup is usually just responsible for verifying it exists.
    """
    self.logger.debug(
        "%s.setup()->connections to an external process" % (self.__class__.__name__)
    )

    # Having this in setup means the workthread should always be running. 
    self.work_proc = Process(
        target=self.work_func, 
        args=(self.comp_condition, self.__volatile_status__), 
        kwargs=self.additional_args
    )
    self.work_proc.start()
    atexit.register(self.work_proc.terminate)  # TODO(josh): make sure this does what we think it doess: cleans up resources when it dies

  def initialise(self) -> None:
    """ 
    Initialise configures and resets the behaviour ready for (repeated) execution
    """
    self.logger.debug(f"Initliazing {self.name}...")
    self.__volatile_status__.set_value(py_trees.common.Status.RUNNING)
    self.work_gate.set()

  def update(self) -> py_trees.common.Status:
    """Increment the counter, monitor and decide on a new status."""
    self.logger.debug(f"Getting tick on {self.name}. Staus: {self.__volatile_status__.get_value()}")

    # This does the interprocess communcication between this thread which is getting ticked and the work_proc thread which is doing work
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
        # TODO: should clear even here so work thread can go back to wait state
        # self.work_gate.clear()

    return new_status

  def terminate(self, new_status: py_trees.common.Status) -> None:
      """Nothing to clean up in this example."""
      print(f"TERMINATE CALLED ON {self.name}, pid: {os.getpid()}")
      if self.work_proc.is_alive():
        print(f"The process is still alive on {os.getpid()}")
        self.work_proc.terminate()
        self.logger.debug(
            py_trees.console.red + "%s.terminate()[%s->%s]"
            % (self.__class__.__name__, self.status, new_status)
        )


if __name__ == '__main__':
  pass
