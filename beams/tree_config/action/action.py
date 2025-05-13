import logging
from dataclasses import dataclass, field

import py_trees
from epics import caget, caput

from beams.behavior_tree.action_node import ActionNode, wrapped_action_work
from beams.tree_config.base import BaseItem

from beams.devices

logger = logging.getLogger(__name__)

@dataclass
class FindReticuleTransform(BaseItem):
  
  camera_prefix: str = ""

  def get_tree(self) -> ActionNode:

    @wrapped_action_work
    def work_func(comp_condition: Evaluatable) -> py_trees.common.Status:

