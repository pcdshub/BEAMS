from collections.abc import Collection
from dataclasses import dataclass, field
from uuid import UUID, uuid4
from apischema import ValidationError, deserialize, serialize
from apischema.json_schema import deserialization_schema
from typing import Optional, List, Union
from enum import Enum
import json
import time

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
  INC = "INC"
  SET = "SET"


# Define a schema with standard dataclasses
@dataclass
class _NodeEntry:
  # id: UUID
  name: str
  # n_type: NodeType
  
  # def get_tree(self):
  #     raise NotImplementedError("Cannot get tree from abstract base class!") 


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
  Mode: CheckAndDoNodeTypeMode  # TODO: should be enum
  Value: int


@dataclass
class CheckAndDoNodeEntry(_NodeEntry):
  check_and_do_type: CheckAndDoNodeType
  check_entry: CheckEntry
  do_entry: DoEntry
  n_type : NodeType = NodeType.CHECKandDO


  def get_tree(self):
      if self.check_and_do_type == CheckAndDoNodeType.CHECKPV:
        # Work function generator for DO of check and do
        def update_pv(comp_condition, volatile_status, **kwargs):
          value = 0
          while not comp_condition(value):
            value = caget(self.check_entry.Pv)
            if value >= 100:
              volatile_status.set_value(py_trees.common.Status.SUCCESS)
            py_trees.console.logdebug(f"Value is {value}, BT Status: {volatile_status.get_value()}")
            caput(self.do_entry.Pv, value + 10)
            time.sleep(1)
        
        # Build Check Node
        check_lambda = lambda : caget(self.check_entry.Pv) >= self.check_pv.Thresh
        condition_node = ConditionNode(f"{self.name}_check", check_lambda)


        # Build Do Node
        comp_cond = lambda x: x > self.check_pv.Thresh
        action_node = ActionNode(f"{self.name}_do", update_pv, comp_cond)

