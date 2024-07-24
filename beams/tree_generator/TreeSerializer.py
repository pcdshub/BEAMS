from collections.abc import Collection
from dataclasses import dataclass, field
from uuid import UUID, uuid4
from apischema import ValidationError, deserialize, serialize
from apischema.json_schema import deserialization_schema
from typing import Optional, List, Union
from enum import Enum
from multiprocessing import Event, Lock
import json
import time
import os

from epics import caput, caget
import py_trees


from beams.behavior_tree.ActionNode import ActionNode
from beams.behavior_tree.CheckAndDo import CheckAndDo
from beams.behavior_tree.ConditionNode import ConditionNode


class CheckAndDoNodeTypeMode(Enum):
  INC = "INC"  # self.Value will be interpreted as the value to INCREMENT the current value by
  SET = "SET"  # self.Value will be interpreted as the value to SET the current value to


# Define a schema with standard dataclasses
@dataclass
class _NodeEntry:
  name: str
  
  def get_tree(self):
      raise NotImplementedError("Cannot get tree from abstract base class!") 


@dataclass
class ActionNodeEntry(_NodeEntry):
  
  class ActionNodeType(Enum):
    CHECKPV = "CheckPV"


@dataclass
class ConditonNodeEntry(_NodeEntry):

  class ConditionNodeType(Enum):
    CHECKPV = "CheckPV"


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

  class CheckAndDoNodeType(Enum):
    CHECKPV = "CheckPV"

  check_and_do_type: CheckAndDoNodeType
  check_entry: CheckEntry
  do_entry: DoEntry

  def get_tree(self):
      if (self.check_and_do_type == CheckAndDoNodeEntry.CheckAndDoNodeType.CHECKPV):
        # Determine what the lambda will caput:
        caput_lambda = lambda : 0
        # if we are in increment mode, produce a function that can increment current value
        if (self.do_entry.Mode == CheckAndDoNodeTypeMode.INC):
          caput_lambda = lambda x : x + self.do_entry.Value
        # if we are in set mode just set it to a value
        elif (self.do_entry.Mode == CheckAndDoNodeTypeMode.SET):
          caput_lambda = lambda x : self.do_entry.Value

        wait_for_tick = Event()
        wait_for_tick_lock = Lock()

        # Work function generator for DO of check and do
        def update_pv(comp_condition, volatile_status, **kwargs):
          py_trees.console.logdebug(f"WAITING FOR INIT {os.getpid()} from node: {self.name}")
          wait_for_tick.wait()

          # Set to running
          
          value = 0
          while not comp_condition(value):  # TODO check work_gate.is_set()
            py_trees.console.logdebug(f"CALLING CAGET FROM {os.getpid()} from node: {self.name}")
            value = caget(self.check_entry.Pv)
            if (value >= self.check_entry.Thresh):  # TODO: we are implicitly connecting the check thresh value with the lamda produced from the do. Maybe fix
              volatile_status.set_value(py_trees.common.Status.SUCCESS)
            py_trees.console.logdebug(f"{self.name}: Value is {value}, BT Status: {volatile_status.get_value()}")
            caput(self.do_entry.Pv, caput_lambda(value))
            time.sleep(0.1)  # TODO(josh): this is a very important hard coded constant, reflcect on where to place with more visibility
        
        # TODO: here is where we can build more complex trees
        # Build Check Node
        check_lambda = lambda : caget(self.check_entry.Pv) >= self.check_entry.Thresh
        condition_node = ConditionNode(f"{self.name}_check", check_lambda)

        # Build Do Node
        comp_cond = lambda check_val: check_val > self.check_entry.Thresh
        action_node = ActionNode(name=f"{self.name}_do", 
                                 work_func=update_pv, 
                                 completion_condition=comp_cond, 
                                 work_gate=wait_for_tick,
                                 work_lock=wait_for_tick_lock)

        check_and_do_node = CheckAndDo(f"{self.name}_check_and_do_root", condition_node, action_node)
        check_and_do_node.setup()

        return check_and_do_node


# TODO: Ask if we want this and beams.beahvior_tree.CheckAndDo to share a baseclass...
@dataclass
class TreeSpec():
  name : str
  children: Optional[List[CheckAndDoNodeEntry]] = None

  def get_tree(self):
    children_trees = [x.get_tree().root for x in self.children]
    print(children_trees)
    self.root = py_trees.composites.Sequence(self.name, memory=True)
    self.root.add_children(children_trees)
    self.setup()
    return self

  def setup(self):
    self.root.setup_with_descendants()
