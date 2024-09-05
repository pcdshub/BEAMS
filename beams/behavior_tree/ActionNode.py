import atexit
import logging
import os
from multiprocessing import Event, Queue
from typing import Any, Callable, Optional

import py_trees

from beams.behavior_tree.ActionWorker import ActionWorker
from beams.behavior_tree.VolatileStatus import VolatileStatus

logger = logging.getLogger(__name__)


class ActionNode(py_trees.behaviour.Behaviour):
    def __init__(
        self,
        name: str,
        work_func: Callable[[Any], None],
        completion_condition: Callable[[Any], bool],
        work_gate: Optional[Event] = None,
    ):
        # TODO: can add failure condition argument...
        super().__init__(name)
        self.volatile_status = VolatileStatus(self.status)
        # TODO: may want to instantiate these locally and then decorate
        # the passed work function with them
        self.work_gate = work_gate or Event()
        self.completion_condition = completion_condition
        self.work_func = work_func
        logger.debug(f'creating worker from {os.getpid()}')
        self.worker = ActionWorker(
            proc_name=name,
            volatile_status=self.volatile_status,
            work_func=self.work_wrapper,
            comp_cond=completion_condition,
            stop_func=None
        )  # TODO: some standard notion of stop function could be valuable
        self.logger.debug("%s.__init__()" % (self.__class__.__name__))

    def work_wrapper(
        self,
        volatile_status: VolatileStatus,
        log_queue: Queue,
        log_configurer: Callable) -> None:
        """
        Wrap self.work_func, and set up logging / status communication
        InterProcess Communication performed by shared memory objects:
        - volatile status
        - logging queue

        Runs a persistent while loop, in which the work func is called repeatedly
        """
        log_configurer(log_queue)
        logger.debug(f"WAITING FOR INIT from node: {self.name}")
        self.work_gate.wait()

        # Set to running
        volatile_status.set_value(py_trees.common.Status.RUNNING)
        while not self.completion_condition():
            logger.debug(f"CALLING CAGET FROM from node ({self.name})")
            status = self.work_func(self.completion_condition)
            volatile_status.set_value(status)
            logger.debug(f"Setting node ({self.name}): {volatile_status.get_value()}")

        # one last check
        if self.completion_condition():
            volatile_status.set_value(py_trees.common.Status.SUCCESS)
        else:
            volatile_status.set_value(py_trees.common.Status.FAILURE)

        logger.debug(f"Worker for node ({self.name}) completed.")

    def setup(self, **kwargs: int) -> None:
        """Kickstart the separate process this behaviour will work with.
        Ordinarily this process will be already running. In this case,
        setup is usually just responsible for verifying it exists.
        """
        logger.debug(
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
        logger.debug(f"Initliazing {self.name}...")
        self.volatile_status.set_value(py_trees.common.Status.RUNNING)
        self.work_gate.set()

    def update(self) -> py_trees.common.Status:
        """Increment the counter, monitor and decide on a new status."""
        logger.debug(
            f"Getting tick on {self.name}. "
            f"Status: {self.volatile_status.get_value()}"
        )

        # This does the interprocess communcication between this thread which is
        # getting ticked and the work_proc thread which is doing work
        new_status = self.volatile_status.get_value()

        if new_status == py_trees.common.Status.SUCCESS:
            self.feedback_message = "Processing finished"
            logger.debug(
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
        """Nothing to clean up."""
        logger.debug(
            py_trees.console.red
            + "%s.terminate()[%s->%s]"
            % (self.__class__.__name__, self.status, new_status)
            + py_trees.console.reset
        )
