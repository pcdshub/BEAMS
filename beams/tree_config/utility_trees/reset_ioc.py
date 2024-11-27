import logging
from dataclasses import dataclass
from sys import maxsize as MAX_INT

import py_trees
from epics import caget
from py_trees.composites import Sequence

from beams.behavior_tree.action_node import ActionNode, wrapped_action_work
from beams.typing_helper import Evaluatable
from beams.tree_config.action import SetPVActionItem
from beams.tree_config.base import BaseItem
from beams.tree_config.condition import BinaryConditionItem, ConditionOperator
from beams.tree_config.value import ProcessIntValue, EPICSValue

logger = logging.getLogger(__name__)


@dataclass
class ResetIOCItem(BaseItem):
    ioc_prefix: str = ""
    # semi static member objects
    HEARTBEAT_POSTFIX: str = ":HEARTBEAT"
    SYSRESET_POSTFIX: str = ":SysReset"
    HEARTBEAT_KEY_NAME: str = "heartbeat"

    def __post_init__(self):
        # non dataclass PVss
        self.hbeat_val = ProcessIntValue(value=-1)
        self.name = f"{self.ioc_prefix}_reset_tree"

    def get_tree(self) -> Sequence:
        def check_acquired_current_hbeat():
            val = self.hbeat_val.get_value() != -1
            logger.debug(f"GOT CURRENT HBEAT AS {val}, {self.hbeat_val.get_value()}")
            return val

        # get the current heartbeat of IOC
        @wrapped_action_work(loop_period_sec=1.0)
        def cache_hbeat_wfunc(comp_condition: Evaluatable) -> py_trees.common.Status:
            current_hbeat = caget(self.ioc_prefix+self.HEARTBEAT_POSTFIX)
            self.hbeat_val.set_value(current_hbeat)
            logger.debug(f"<<-- Aquired ioc: {self.ioc_prefix} hbeat count: {current_hbeat} and put to blackboard")

            return py_trees.common.Status.SUCCESS

        cache_current_heartbeat = ActionNode(name=f"{self.ioc_prefix}_hbeat_cache",
                                             work_func=cache_hbeat_wfunc,
                                             completion_condition=check_acquired_current_hbeat
                                             )

        # send the reset command
        reset_success_termination_condiiton = BinaryConditionItem(
                                                left_value=EPICSValue(pv_name=f"{self.ioc_prefix+self.HEARTBEAT_POSTFIX}"),
                                                right_value=self.hbeat_val,
                                                operator=ConditionOperator.less)
        send_reset = SetPVActionItem(name=f"reset_{self.ioc_prefix}",
                                     pv=f"{self.ioc_prefix}:SysReset",
                                     value=1,
                                     loop_period_sec=1.0,  # this is greater than work_timeout period, should only happen once.
                                     termination_check=reset_success_termination_condiiton)

        root = Sequence(name=self.name,
                        memory=True,
                        children=[cache_current_heartbeat, send_reset.get_tree()])
        return root
