from collections.abc import Collection
from dataclasses import dataclass, field
from uuid import UUID, uuid4
from apischema import ValidationError, deserialize, serialize
from apischema.json_schema import deserialization_schema
from typing import Optional, List, Union
from enum import Enum
import json
import time

from epics import caput, caget
import py_trees


from beams.behavior_tree.ActionNode import ActionNode
from beams.behavior_tree.CheckAndDo import CheckAndDo
from beams.behavior_tree.ConditionNode import ConditionNode

config_file_name = "config.json"


# Define the ContactType enum
class NodeType(Enum):
  ACTION = "Action"
  CONDITION = "Condition"
  CHECKandDO = "CheckAndDo"
  NONE = "None"


class ActionNodeType(Enum):
  CHECKPV = "CheckPV"


class ConditionNodeType(Enum):
  CHECKPV = "CheckPV"


class CheckAndDoNodeType(Enum):
  CHECKPV = "CheckPV"


class CheckAndDoNodeTypeMode(Enum):
  INC = "INC"  # self.Value will be interpreted as the value to INCREMENT the current value by
  SET = "SET"  # self.Value will be interpreted as the value to SET the current value to


# Define a schema with standard dataclasses
@dataclass
class _NodeEntry:
  # id: UUID  # TODO: in the future use as a hash / version control mechanism per document
  name: str
  # n_type: NodeType  # TODO: python is toilsome and makes inheritence weird sometimes. More related to apischema in this case but still sucks
  
  def get_tree(self):
      raise NotImplementedError("Cannot get tree from abstract base class!") 


@dataclass
class ActionNodeEntry(_NodeEntry):
  n_type : NodeType = NodeType.ACTION


@dataclass
class ConditonNodeEntry(_NodeEntry):
  n_type : NodeType = NodeType.CONDITION


@dataclass
class CheckEntry():
  Pv: str
  Thresh: int


@dataclass
class DoEntry():
  Pv: str
  Mode: CheckAndDoNodeTypeMode
  Value: int


@dataclass
class CheckAndDoNodeEntry(_NodeEntry):
  check_and_do_type: CheckAndDoNodeType
  check_entry: CheckEntry
  do_entry: DoEntry
  n_type : NodeType = NodeType.CHECKandDO
  children: Optional[List[_NodeEntry]] = None

  def get_tree(self):
      if (self.check_and_do_type == CheckAndDoNodeType.CHECKPV):
        # Determine what the lambda will caput:
        caput_lambda = lambda : 0
        print(f"DO ENTRY MOOOODE: {self.do_entry.Mode}")
        # if we are in increment mode, produce a function that can increment current value
        if (self.do_entry.Mode == CheckAndDoNodeTypeMode.INC):
          caput_lambda = lambda x : x + self.do_entry.Value
        # if we are in set mode just set it to a value
        elif (self.do_entry.Mode == CheckAndDoNodeTypeMode.SET):
          caput_lambda = lambda x : self.do_entry.Value

        # Work function generator for DO of check and do
        def update_pv(comp_condition, volatile_status, **kwargs):
          value = 0
          while not comp_condition(value):
            value = caget(self.check_entry.Pv)
            if (value >= self.check_entry.Thresh):  # TODO: we are implicitly connecting the check thresh value with the lamda produced from the do. Maybe fix
              volatile_status.set_value(py_trees.common.Status.SUCCESS)
            py_trees.console.logdebug(f"Value is {value}, BT Status: {volatile_status.get_value()}")
            caput(self.do_entry.Pv, caput_lambda(value))
            time.sleep(0.01)
        
        # TODO: here is where we can build more complex trees
        # Build Check Node
        check_lambda = lambda : caget(self.check_entry.Pv) >= self.check_entry.Thresh
        condition_node = ConditionNode(f"{self.name}_check", check_lambda)

        # Build Do Node
        comp_cond = lambda check_val: check_val > self.check_entry.Thresh
        action_node = ActionNode(f"{self.name}_do", update_pv, comp_cond)

        check_and_do_node = CheckAndDo(f"{self.name}_check_and_do_root", condition_node, action_node)
        check_and_do_node.setup()

        return check_and_do_node
