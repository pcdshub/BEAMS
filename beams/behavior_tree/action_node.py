import atexit
import logging
from multiprocessing import Event

import py_trees

from beams.behavior_tree.action_worker import wrapped_action_work  # noqa: F401
from beams.behavior_tree.action_worker import ActionWorker
from beams.behavior_tree.volatile_status import VolatileStatus
from beams.typing_helper import ActionNodeWorkLoop, Evaluatable

logger = logging.getLogger(__name__)


class ActionNode(py_trees.behaviour.Behaviour):
    def __init__(
        self,
        name: str,
        work_func: ActionNodeWorkLoop,
        completion_condition: Evaluatable
    ):
        # TODO: can add failure condition argument...
        super().__init__(name)
        self.volatile_status = VolatileStatus(self.status)
        # TODO: may want to instantiate these locally and then decorate
        # the passed work function with them
        self.work_gate = Event()
        self.completion_condition = completion_condition
        self.work_func = work_func
        self.worker = ActionWorker(
            proc_name=name,
            volatile_status=self.volatile_status,
            work_gate=self.work_gate,
            work_func=self.work_func,
            comp_cond=completion_condition,
            stop_func=None
        )  # TODO: some standard notion of stop function could be valuable
        self.is_set_up = False

    def setup(self, **kwargs: int) -> None:
        """Kickstart the separate process this behaviour will work with.
        Ordinarily this process will be already running. In this case,
        setup is usually just responsible for verifying it exists.
        """
        # Having this in setup means the workthread should always be running.
        self.worker.start_work()
        atexit.register(
            self.shutdown
        )  # TODO(josh): make sure this cleans up resources when it dies
        self.is_set_up = True

    # https://py-trees.readthedocs.io/en/devel/modules.html#py_trees.behaviour.Behaviour.shutdown
    def shutdown(self) -> None:
        if self.is_set_up:
            self.worker.stop_work()
            logger.debug("Work process joined")
            self.is_set_up = False

    def initialise(self) -> None:
        """
        Initialise configures and resets the behaviour ready for (repeated) execution
        """
        self.volatile_status.set_value(py_trees.common.Status.RUNNING)
        logger.debug(f"{self.name}.initialise [{self.status.name}->RUNNING]")
        self.work_gate.set()

    def update(self) -> py_trees.common.Status:
        """Increment the counter, monitor and decide on a new status."""
        logger.debug(f"{self.name}.update [{self.status.name}]")

        # This does the interprocess communcication between this thread which is
        # getting ticked and the work_proc thread which is doing work
        new_status = self.volatile_status.get_value()

        if new_status == py_trees.common.Status.SUCCESS:
            self.feedback_message = "Processing finished"
            logger.debug(
                f"{self.name}.update [{self.status.name}->{new_status.name}] "
                f"{self.feedback_message}"
            )
            # TODO: should clear even here so work thread can go back to wait state
            # self.work_gate.clear()

        return new_status

    def terminate(self, new_status: py_trees.common.Status) -> None:
        """Nothing to clean up."""
        logger.debug(
            "%s.terminate [%s->%s]"
            % (self.name, self.status.name, new_status.name)
        )
