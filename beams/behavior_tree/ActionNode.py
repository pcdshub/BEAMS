import time
import atexit
import logging
import os
from multiprocessing import Event, Queue, Value
from typing import Any, Callable

import py_trees

from beams.behavior_tree.ActionWorker import ActionWorker
from beams.behavior_tree.VolatileStatus import VolatileStatus

logger = logging.getLogger(__name__)


def wrapped_action_work(loop_period_sec: float = 0.1):
    def inner_decorator_generator(func):
        def work_wrapper(
            do_work: Value,
            name: str,
            work_gate: Event,
            volatile_status: VolatileStatus,
            completion_condition: Callable[[Any], bool],
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
            while (do_work.value):
                logger.debug(f"WAITING FOR INIT from node: {name}")
                work_gate.wait()
                work_gate.clear()
                
                # Set to running
                volatile_status.set_value(py_trees.common.Status.RUNNING)
                while not completion_condition():
                    logger.debug(f"CALLING CAGET FROM from node ({name})")
                    try:
                        status = func(completion_condition)
                    except Exception as ex:
                        volatile_status.set_value(py_trees.common.Status.FAILURE)
                        logger.error(f"Work function failed, setting node ({name}) "
                                     f"as FAILED. ({ex})")
                        break

                    volatile_status.set_value(status)
                    logger.debug(f"Setting node ({name}): {volatile_status.get_value()}")
                    time.sleep(loop_period_sec)

                # one last check
                if completion_condition():
                    volatile_status.set_value(py_trees.common.Status.SUCCESS)
                else:
                    volatile_status.set_value(py_trees.common.Status.FAILURE)

                logger.debug(f"Worker for node ({name}) completed.")
        return work_wrapper
    return inner_decorator_generator


class ActionNode(py_trees.behaviour.Behaviour):
    def __init__(
        self,
        name: str,
        work_func: Callable[[Any], None],
        completion_condition: Callable[[Any], bool]
    ):
        # TODO: can add failure condition argument...
        super().__init__(name)
        self.volatile_status = VolatileStatus(self.status)
        # TODO: may want to instantiate these locally and then decorate
        # the passed work function with them
        self.work_gate = Event()
        self.completion_condition = completion_condition
        self.work_func = work_func
        logger.debug(f'creating worker from {os.getpid()}')
        self.worker = ActionWorker(
            proc_name=name,
            volatile_status=self.volatile_status,
            work_gate=self.work_gate,
            work_func=self.work_func,
            comp_cond=completion_condition,
            stop_func=None
        )  # TODO: some standard notion of stop function could be valuable
        logger.debug("%s.__init__()" % (self.__class__.__name__))

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
