import logging
from ctypes import c_bool
from multiprocessing import Value
from typing import Callable, List

import py_trees

logger = logging.getLogger(__name__)


class ConditionNode(py_trees.behaviour.Behaviour):
    def __init__(self, name, condition: Callable[[], bool], *args):
        super().__init__(name)
        self.condition = condition  # condition to be evaluated
        self.condition_args = args

    def update(self):
        state = self.condition(*self.condition_args)
        # we take true to mean success
        if state is True:
            status = py_trees.common.Status.SUCCESS
        else:
            status = py_trees.common.Status.FAILURE
        logger.debug(f"{self.name}.update [{status.name}]")

        return status


'''
Specialty Condition Node that waits for external programatic ACK to continue
'''


class AckConditionNode(py_trees.behaviour.Behaviour):
    def __init__(self, name, permisible_user_list, unset_on_check):
        super().__init__(name)
        self.permisible_users: List[str] = permisible_user_list
        self.is_acknowledged = Value(c_bool, False)
        self.acknowleding_user = "NO USER"
        self.unset_on_check = unset_on_check

    def acknowledge_node(self, user_name):
        if user_name in self.permisible_users:
            self.is_acknowledged.value = True
            self.acknowleding_user = user_name
            logger.debug(f"User: {user_name} successfully acknowledged node: {self.name}")
        else:
            logger.debug(f"User: {user_name} failed to acknowledged node: {self.name}, not in permisible_user_list: {self.permisible_users}")

    def check_ack(self):
        return_value = self.is_acknowledged.value
        if self.unset_on_check:
            logger.debug(f"Ack node: {self.name} has been checked with value {return_value} and reset.")
            self.is_acknowledged.value = False
        return return_value

    def update(self):
        ack = self.check_ack()
        # we take true to mean success
        if ack is True:
            status = py_trees.common.Status.SUCCESS
        else:
            status = py_trees.common.Status.FAILURE
        logger.debug(f"{self.name}.update [{status.name}]")

        return status
