import logging
from dataclasses import dataclass, field

import py_trees
from py_trees.composites import Selector

from beams.behavior_tree.action_node import ActionNode, wrapped_action_work
from beams.behavior_tree.check_and_do import CheckAndDo

from beams.tree_config.base import BaseItem
from beams.tree_config.condition import AcknowledgeConditionItem
from beams.typing_helper import Evaluatable

logger = logging.getLogger(__name__)


@dataclass
class WaitForAckNodeItem(BaseItem):
    ack_cond_item: AcknowledgeConditionItem = field(default_factory=AcknowledgeConditionItem)
    wait_time_out: int = 60

    def get_tree(self) -> Selector:
        
        check_node = self.ack_cond_item.get_tree()

        # check if node is acked
        def check_acked() -> bool:
            return check_node.check_ack()

        # build waiting action node #TODO: probably put timeout here
        @wrapped_action_work(loop_period_sec=0.1, work_function_timeout_period_sec=self.wait_time_out)
        def wait_for_ack_work(comp_condition: Evaluatable) -> py_trees.common.Status:
            if comp_condition():
                return py_trees.common.Status.SUCCESS
            else:
                return py_trees.common.Status.RUNNING

        wait_action_node = ActionNode(name=f"{self.name}_waiter_action",
                                      work_func=wait_for_ack_work,
                                      completion_condition=check_acked
                                      )

        return CheckAndDo(name=f"{self.name}_wait_for_ack",
                          check=check_node,
                          do=wait_action_node)
