import logging
from typing import Callable

import py_trees

logger = logging.getLogger(__name__)


class ConditionNode(py_trees.behaviour.Behaviour):
    def __init__(self, name, condition: Callable[[], bool], *args):
        super().__init__(name)
        self.condition = condition  # condition to be evaluated
        logger.debug("%s.__init__()" % (self.__class__.__name__))
        self.condition_args = args

    def update(self):
        state = self.condition(*self.condition_args)
        # we take true to mean success
        if state is True:
            status = py_trees.common.Status.SUCCESS
        else:
            status = py_trees.common.Status.FAILURE
        logger.debug(
            py_trees.console.cyan
            + f"Ticking: {self.name} results in {status}"
            + py_trees.console.reset
        )

        return status
