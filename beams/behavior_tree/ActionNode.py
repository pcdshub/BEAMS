import atexit
import os
from multiprocessing import Event, Lock
from typing import Callable, Any, Optional, Union

import py_trees
from epics.multiproc import CAProcess

from beams.behavior_tree.ActionWorker import ActionWorker
from beams.behavior_tree.VolatileStatus import VolatileStatus


class ActionNode(py_trees.behaviour.Behaviour):
    def __init__(
        self,
        name: str,
        work_func: Callable[[Any], None],
        completion_condition: Callable[[Any], bool],
        work_gate=Event(),
        work_lock=Lock(),
        **kwargs,
    ):  # TODO: can add failure condition argument...
        super(ActionNode, self).__init__(name)
        # print(type(self.status))
        self.__volatile_status__ = VolatileStatus(self.status)
        # TODO may want to instantiate these locally and then decorate the passed work function with them
        self.work_gate = work_gate
        self.lock = work_lock
        self.worker = ActionWorker(proc_name=name,
                                   volatile_status=self.__volatile_status__,
                                   work_func=work_func,
                                   comp_cond=completion_condition,
                                   stop_func=None
                                   )  # TODO: some standard notion of stop function could be valuable
        self.logger.debug("%s.__init__()" % (self.__class__.__name__))

    def setup(self, **kwargs: int) -> None:
        """Kickstart the separate process this behaviour will work with.
        Ordinarily this process will be already running. In this case,
        setup is usually just responsible for verifying it exists.
        """
        self.logger.debug(
            "%s.setup()->connections to an external process" % (self.__class__.__name__)
        )

        # Having this in setup means the workthread should always be running.
        self.worker.start_work()
        atexit.register(
            self.worker.stop_work
        )  # TODO(josh): make sure this cleans up resources when it dies

    def initialise(self) -> None:
        """
        Initialise configures and resets the behaviour ready for (repeated) execution
        """
        self.logger.debug(f"Initliazing {self.name}...")
        self.__volatile_status__.set_value(py_trees.common.Status.RUNNING)
        self.work_gate.set()

    def update(self) -> py_trees.common.Status:
        """Increment the counter, monitor and decide on a new status."""
        self.logger.debug(
            f"Getting tick on {self.name}. "
            f"Status: {self.__volatile_status__.get_value()}"
        )

        # This does the interprocess communcication between this thread which is
        # getting ticked and the work_proc thread which is doing work
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

    # TODO: serious introspection about that we want to do here. 
    # def terminate(self, new_status: py_trees.common.Status) -> None:
    #     """Nothing to clean up in this example."""
    #     print(f"TERMINATE CALLED ON {self.name}, pid: {os.getpid()}")
    #     if self.work_proc.is_alive():
    #         print(f"The process is still alive on {os.getpid()}")
    #         self.work_proc.terminate()
    #         self.logger.debug(
    #             py_trees.console.red
    #             + "%s.terminate()[%s->%s]"
    #             % (self.__class__.__name__, self.status, new_status)
    #         )


if __name__ == "__main__":
    pass
