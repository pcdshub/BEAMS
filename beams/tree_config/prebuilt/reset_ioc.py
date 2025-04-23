import logging
from dataclasses import dataclass

import py_trees
from epics import caget
from py_trees.composites import Sequence

from beams.behavior_tree.action_node import ActionNode, wrapped_action_work
from beams.tree_config.action.pv_action import SetPVActionItem
from beams.tree_config.base import BaseItem
from beams.tree_config.condition import BinaryConditionItem, ConditionOperator
from beams.tree_config.value import EPICSValue, ProcessIntValue
from beams.typing_helper import Evaluatable

logger = logging.getLogger(__name__)


@dataclass
class ResetIOCItem(BaseItem):
    ioc_prefix: str = ""
    # semi static member objects
    HEARTBEAT_SUFFIX: str = ":HEARTBEAT"
    SYSRESET_SUFFIX: str = ":SysReset"
    HEARTBEAT_KEY_NAME: str = "heartbeat"

    def __post_init__(self):
        # non dataclass PVss
        self.hbeat_val = ProcessIntValue(value=-1)  # set to unachievable heartbeat val
        if not self.name:
            self.name = f"{self.ioc_prefix}_reset_tree"

    def get_tree(self) -> Sequence:
        def check_acquired_current_hbeat():
            has_hearbeat_been_cached = self.hbeat_val.get_value() != -1  # set to unachievable heartbeat val
            logger.debug(f"Heartbeat cached as {has_hearbeat_been_cached}, {self.hbeat_val.get_value()}")
            return has_hearbeat_been_cached

        # get the current heartbeat of IOC
        @wrapped_action_work(loop_period_sec=0.1)
        def cache_hbeat_wfunc(comp_condition: Evaluatable) -> py_trees.common.Status:
            current_hbeat = caget(self.ioc_prefix+self.HEARTBEAT_SUFFIX)
            self.hbeat_val.set_value(current_hbeat)
            logger.debug(f"<<-- Aquired ioc hbeat: {self.ioc_prefix} hbeat count: {current_hbeat}")

            return py_trees.common.Status.SUCCESS

        cache_current_heartbeat = ActionNode(name=f"{self.ioc_prefix}_hbeat_cache",
                                             work_func=cache_hbeat_wfunc,
                                             completion_condition=check_acquired_current_hbeat
                                             )

        # send the reset command
        reset_success_termination_condiiton = BinaryConditionItem(
            left_value=EPICSValue(pv_name=f"{self.ioc_prefix+self.HEARTBEAT_SUFFIX}"),
            right_value=self.hbeat_val,
            operator=ConditionOperator.less
        )
        send_reset = SetPVActionItem(
            name=f"reset_{self.ioc_prefix}",
            pv=f"{self.ioc_prefix}{self.SYSRESET_SUFFIX}",
            value=1,
            loop_period_sec=0.1,  # this is greater than work_timeout period, should only happen once.
            termination_check=reset_success_termination_condiiton
        )

        root = Sequence(name=self.name,
                        memory=True,
                        children=[cache_current_heartbeat, send_reset.get_tree()])
        return root
