import logging
from dataclasses import dataclass, field
from typing import Any

import py_trees
from epics import caget, caput

from beams.behavior_tree.action_node import ActionNode, wrapped_action_work
from beams.tree_config.base import BaseItem
from beams.tree_config.condition import BaseConditionItem, DummyConditionItem
from beams.typing_helper import Evaluatable

logger = logging.getLogger(__name__)


@dataclass
class SetPVActionItem(BaseItem):
    pv: str = ""
    value: Any = 1
    loop_period_sec: float = 1.0

    termination_check: BaseConditionItem = field(default_factory=DummyConditionItem)

    def get_tree(self) -> ActionNode:

        @wrapped_action_work(self.loop_period_sec)
        def work_func(comp_condition: Evaluatable) -> py_trees.common.Status:
            try:
                # Set to running
                # double caget, this is uneeded as currently the comp_condition
                # has caget baked in
                value = caget(self.pv)

                if comp_condition():
                    return py_trees.common.Status.SUCCESS
                logger.debug(f" <<-- ({self.name}): {self.pv} = {value}")

                # specific caput logic to SetPVActionItem
                caput(self.pv, self.value)
                return py_trees.common.Status.RUNNING
            except Exception as ex:
                logger.warning(f" <<-- ({self.name}): work failed, {ex}")
                return py_trees.common.Status.FAILURE

        comp_cond = self.termination_check.get_condition_function()

        node = ActionNode(
            name=self.name,
            work_func=work_func,
            completion_condition=comp_cond,
        )

        return node


@dataclass
class IncPVActionItem(BaseItem):
    pv: str = ""
    increment: float = 1
    loop_period_sec: float = 1.0

    termination_check: BaseConditionItem = field(default_factory=DummyConditionItem)

    def get_tree(self) -> ActionNode:

        @wrapped_action_work(self.loop_period_sec)
        def work_func(comp_condition: Evaluatable) -> py_trees.common.Status:
            """
            To be run inside of a while loop
            Action node should take care of logging, reporting status
            """
            try:
                value = caget(self.pv)

                logger.debug(f" <<-- ({self.name}): {self.pv} = {value}")
                if comp_condition():
                    return py_trees.common.Status.SUCCESS

                # specific caput logic to IncPVActionItem
                caput(self.pv, value + self.increment)
                return py_trees.common.Status.RUNNING
            except Exception as ex:
                logger.warning(f" <<-- ({self.name}): work failed, {ex}")
                return py_trees.common.Status.FAILURE

        comp_cond = self.termination_check.get_condition_function()

        node = ActionNode(
            name=self.name,
            work_func=work_func,
            completion_condition=comp_cond,
        )

        return node
