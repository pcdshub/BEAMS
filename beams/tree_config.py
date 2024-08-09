from __future__ import annotations

import json
import operator
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from multiprocessing import Event, Lock
from pathlib import Path
from typing import Any, Callable, List, Optional

import py_trees
from apischema import deserialize
from epics import caget, caput
from py_trees.behaviour import Behaviour
from py_trees.common import ParallelPolicy
from py_trees.composites import Parallel, Selector, Sequence

from beams.behavior_tree.ActionNode import ActionNode
from beams.behavior_tree.CheckAndDo import CheckAndDo
from beams.behavior_tree.ConditionNode import ConditionNode
from beams.serialization import as_tagged_union


def get_tree_from_path(path: Path) -> py_trees.trees.BehaviourTree:
    """Deserialize a json file, return the tree it specifies"""
    with open(path, "r") as fd:
        deser = json.load(fd)
        tree_item = deserialize(BehaviorTreeItem, deser)

    return tree_item.get_tree()


@dataclass
class BehaviorTreeItem:
    root: BaseItem

    def get_tree(self) -> py_trees.trees.BehaviourTree:
        return py_trees.trees.BehaviourTree(self.root.get_tree())


@as_tagged_union
@dataclass
class BaseItem:
    name: str = ""
    description: str = ""

    def get_tree(self) -> Behaviour:
        """Get the tree node that this dataclass represents"""
        raise NotImplementedError


@dataclass
class ExternalItem(BaseItem):
    path: str = ""

    def get_tree(self) -> Behaviour:
        # grab file
        # de-serialize tree, return it
        raise NotImplementedError


class ParallelMode(Enum):
    """Simple enum mimicing the ``py_trees.common.ParallelPolicy`` options"""

    Base = "Base"
    SuccessOnAll = "SuccesOnAll"
    SuccessOnONe = "SuccessOnOne"
    SuccessOnSelected = "SuccessOnSelected"


@dataclass
class ParallelItem(BaseItem):
    policy: ParallelMode = ParallelMode.Base
    children: Optional[List[BaseItem]] = field(default_factory=list)

    def get_tree(self) -> Parallel:
        children = []
        for child in self.children:
            children.append(child.get_tree())

        node = Parallel(
            name=self.name,
            policy=getattr(ParallelPolicy, self.policy.value),
            children=children,
        )

        return node


@dataclass
class SelectorItem(BaseItem):
    """aka fallback node"""

    memory: bool = False
    children: Optional[List[BaseItem]] = field(default_factory=list)

    def get_tree(self) -> Selector:
        children = []
        for child in self.children:
            children.append(child.get_tree())

        node = Selector(name=self.name, memory=self.memory, children=children)
        return node


@dataclass
class SequenceItem(BaseItem):
    memory: bool = False
    children: Optional[List[BaseItem]] = field(default_factory=list)

    def get_tree(self) -> Sequence:
        children = []
        for child in self.children:
            children.append(child.get_tree())

        node = Sequence(name=self.name, memory=self.memory, children=children)

        return node


# Custom LCLS-built Behaviors (idioms)
class ConditionOperator(Enum):
    equal = "eq"
    not_equal = "ne"
    less = "lt"
    greater = "gt"
    less_equal = "le"
    greater_equal = "ge"


@dataclass
class ConditionItem(BaseItem):
    pv: str = ""
    value: Any = 1
    operator: ConditionOperator = ConditionOperator.equal

    def get_tree(self) -> ConditionNode:
        cond_func = self.get_condition_function()
        return ConditionNode(self.name, cond_func)

    def get_condition_function(self) -> Callable[[], bool]:
        op = getattr(operator, self.operator.value)

        def cond_func():
            val = caget(self.pv)
            if val is None:
                return False

            return op(val, self.value)

        return cond_func


@as_tagged_union
@dataclass
class ActionItem(BaseItem):
    loop_period_sec: float = 1.0


@dataclass
class SetPVActionItem(ActionItem):
    pv: str = ""
    value: Any = 1

    termination_check: ConditionItem = field(default_factory=ConditionItem)

    def get_tree(self) -> ActionNode:
        wait_for_tick = Event()
        wait_for_tick_lock = Lock()

        def work_func(comp_condition, volatile_status):
            py_trees.console.logdebug(
                f"WAITING FOR INIT {os.getpid()} " f"from node: {self.name}"
            )
            wait_for_tick.wait()

            # Set to running
            value = 0

            # While termination_check is not True
            while not comp_condition():  # TODO check work_gate.is_set()
                py_trees.console.logdebug(
                    f"CALLING CAGET FROM {os.getpid()} from node: " f"{self.name}"
                )
                value = caget(self.termination_check.pv)

                if comp_condition():
                    volatile_status.set_value(py_trees.common.Status.SUCCESS)
                py_trees.console.logdebug(
                    f"{self.name}: Value is {value}, BT Status: "
                    f"{volatile_status.get_value()}"
                )

                # specific caput logic to SetPVActionItem
                caput(self.pv, self.value)
                time.sleep(self.loop_period_sec)

            # one last check
            if comp_condition():
                volatile_status.set_value(py_trees.common.Status.SUCCESS)
            else:
                volatile_status.set_value(py_trees.common.Status.FAILURE)

        comp_cond = self.termination_check.get_condition_function()

        node = ActionNode(
            name=self.name,
            work_func=work_func,
            completion_condition=comp_cond,
            work_gate=wait_for_tick,
            work_lock=wait_for_tick_lock,
        )

        return node


@dataclass
class IncPVActionItem(ActionItem):
    pv: str = ""
    increment: float = 1

    termination_check: ConditionItem = field(default_factory=ConditionItem)

    # TODO: DRY this out a bit
    def get_tree(self) -> ActionNode:
        wait_for_tick = Event()
        wait_for_tick_lock = Lock()

        def work_func(comp_condition, volatile_status):
            py_trees.console.logdebug(
                f"WAITING FOR INIT {os.getpid()} " f"from node: {self.name}"
            )
            wait_for_tick.wait()

            # Set to running
            value = 0

            # While termination_check is not True
            while not comp_condition():  # TODO check work_gate.is_set()
                py_trees.console.logdebug(
                    f"CALLING CAGET FROM {os.getpid()} from node: " f"{self.name}"
                )
                value = caget(self.pv)

                if comp_condition():
                    volatile_status.set_value(py_trees.common.Status.SUCCESS)
                py_trees.console.logdebug(
                    f"{self.name}: Value is {value}, BT Status: "
                    f"{volatile_status.get_value()}"
                )

                # specific caput logic to IncPVActionItem
                caput(self.pv, value + self.increment)
                time.sleep(self.loop_period_sec)

            # one last check
            if comp_condition():
                volatile_status.set_value(py_trees.common.Status.SUCCESS)
            else:
                volatile_status.set_value(py_trees.common.Status.FAILURE)

        comp_cond = self.termination_check.get_condition_function()

        node = ActionNode(
            name=self.name,
            work_func=work_func,
            completion_condition=comp_cond,
            work_gate=wait_for_tick,
            work_lock=wait_for_tick_lock,
        )

        return node


@dataclass
class CheckAndDoItem(BaseItem):
    check: ConditionItem = field(default_factory=ConditionItem)
    do: ActionItem = field(default_factory=ActionItem)

    def get_tree(self) -> CheckAndDo:
        check_node = self.check.get_tree()
        do_node = self.do.get_tree()

        node = CheckAndDo(name=self.name, check=check_node, do=do_node)

        return node
