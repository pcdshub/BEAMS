"""
A worker specialized to execute ActionNode work functions

The primary utility of this "wrapper" class is to maintain the extensibility of the base Worker class.
This is done by using this class to enumerate the "add_args" required by an ActioNode work function
not required by work functions in general. The add_args are as follows:
* proc_name: names spawned process *and* generated BT node
* work_gate: IPC signalling mechanism to spawned work that py_trees initialise() has been called by parent
* volatile_status: IPC signalling mechanism that contains multiproccesing safe BT status
* comp_cond: the Evaluatable function that determines success or failure of BT node
* LOGGER_QUEUE: instance of the logging queue
* worker_logging_configurer: utility functuon to register log queue with handler
"""
import logging
import time
from multiprocessing import Event, Queue, Value
from typing import Callable, Optional

import py_trees
from epics.multiproc import CAProcess

from beams.behavior_tree.volatile_status import VolatileStatus
from beams.logging import LOGGER_QUEUE, worker_logging_configurer
from beams.sequencer.helpers.timer import Timer
from beams.sequencer.helpers.worker import Worker
from beams.typing_helper import (ActionNodeWorkFunction, ActionNodeWorkLoop,
                                 Evaluatable)

logger = logging.getLogger(__name__)


def wrapped_action_work(loop_period_sec: float = 0.1, work_function_timeout_period_sec: float = 2):
    def action_worker_work_function_generator(func: ActionNodeWorkFunction) -> ActionNodeWorkLoop:
        def work_wrapper(
            do_work: Value,
            name: str,
            work_gate: Event,
            volatile_status: VolatileStatus,
            completion_condition: Evaluatable,
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
            work_loop_timeout_timer = Timer(name=name,
                                            timer_period_seconds=work_function_timeout_period_sec,
                                            auto_start=False)
            while (do_work.value):
                logger.debug(f"WAITING FOR INIT from node: {name}")
                work_gate.wait()
                work_gate.clear()

                # Set to running
                volatile_status.set_value(py_trees.common.Status.RUNNING)
                # Start timer
                work_loop_timeout_timer.start_timer()
                while not completion_condition() and not work_loop_timeout_timer.is_elapsed():
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

                # check if we exited loop because we timed out or we succeeded at task
                if completion_condition():
                    logger.debug(f"Worker for node ({name}) completed.")
                    volatile_status.set_value(py_trees.common.Status.SUCCESS)
                else:
                    logger.debug(f"Worker for node ({name}) failed.")
                    volatile_status.set_value(py_trees.common.Status.FAILURE)

        return work_wrapper
    return action_worker_work_function_generator


class ActionWorker(Worker):
    def __init__(
        self,
        proc_name: str,
        volatile_status: VolatileStatus,
        work_gate: Event,
        work_func: Callable[..., None],
        comp_cond: Callable[..., bool],
        stop_func: Optional[Callable[[None], None]] = None
    ):
        super().__init__(
            proc_name=proc_name,
            stop_func=stop_func,
            work_func=work_func,
            proc_type=CAProcess,
            add_args=(proc_name,
                      work_gate,
                      volatile_status,
                      comp_cond,
                      LOGGER_QUEUE,
                      worker_logging_configurer)
        )
        logger.debug(f"Creating worker ({proc_name})")
        # Note: there may be a world where we define a common stop_func here in
        # which case the class may have maintain a reference to voltaile_status and
        # or comp_cond
