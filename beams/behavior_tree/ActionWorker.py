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
from multiprocessing import Event
from typing import Any, Callable, Optional

from epics.multiproc import CAProcess

from beams.behavior_tree.VolatileStatus import VolatileStatus
from beams.logging import LOGGER_QUEUE, worker_logging_configurer
from beams.sequencer.helpers.Worker import Worker


class ActionWorker(Worker):
    def __init__(
        self,
        proc_name: str,
        volatile_status: VolatileStatus,
        work_gate: Event,
        work_func: Callable[[Any], None],
        comp_cond: Callable[[Any], bool],
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

        # Note: there may be a world where we define a common stop_func here in
        # which case the class may have maintain a reference to voltaile_status and
        # or comp_cond
