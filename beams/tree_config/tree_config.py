from __future__ import annotations

import json
import logging
import operator
from copy import copy
from dataclasses import dataclass, field, fields
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional, Union

import py_trees
from apischema import deserialize, serialize
from epics import caget, caput
from py_trees.behaviour import Behaviour
from py_trees.common import ComparisonExpression, ParallelPolicy, Status
from py_trees.composites import Parallel, Selector, Sequence

from beams.behavior_tree.ActionNode import ActionNode, wrapped_action_work
from beams.behavior_tree.CheckAndDo import CheckAndDo
from beams.behavior_tree.ConditionNode import ConditionNode
from beams.serialization import as_tagged_union
from beams.tree_config.base import BaseItem, BehaviorTreeItem
from beams.tree_config.condition import BaseConditionItem, DummyConditionItem
from beams.typing_helper import Evaluatable

logger = logging.getLogger(__name__)


def get_tree_from_path(path: Path) -> py_trees.trees.BehaviourTree:
    """
    Deserialize a json file, return the tree it specifies.

    This can be used internally to conveniently and consistently load
    serialized json files as ready-to-run behavior trees.
    """
    with open(path, "r") as fd:
        deser = json.load(fd)
        tree_item = deserialize(BehaviorTreeItem, deser)

    return tree_item.get_tree()


def save_tree_item_to_path(path: Union[Path, str], root: BaseItem):
    """
    Serialize a behavior tree item to a json file.

    This can be used to generate serialized trees from python scripts.
    The user needs to create various interwoven tree items, pick the
    correct item to be the root node, and then use this function to
    save the serialized file.

    These files are ready to be consumed by get_tree_from_path.
    """
    ser = serialize(BehaviorTreeItem(root=root))

    with open(path, "w") as fd:
        json.dump(ser, fd, indent=2)
        fd.write("\n")


class ParallelMode(Enum):
    """Simple enum mimicing the ``py_trees.common.ParallelPolicy`` options"""

    Base = "Base"
    SuccessOnAll = "SuccesOnAll"
    SuccessOnONe = "SuccessOnOne"
    SuccessOnSelected = "SuccessOnSelected"


@dataclass
class ParallelItem(BaseItem):
    policy: ParallelMode = ParallelMode.Base
    children: List[BaseItem] = field(default_factory=list)

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
    children: List[BaseItem] = field(default_factory=list)

    def get_tree(self) -> Selector:
        children = []
        for child in self.children:
            children.append(child.get_tree())

        node = Selector(name=self.name, memory=self.memory, children=children)
        return node


@as_tagged_union
@dataclass
class BaseSequenceItem(BaseItem):
    memory: bool = False
    children: List[BaseItem] = field(default_factory=list)

    def get_tree(self) -> Sequence:
        children = []
        for child in self.children:
            children.append(child.get_tree())

        node = Sequence(name=self.name, memory=self.memory, children=children)

        return node


@dataclass
class SequenceItem(BaseSequenceItem):
    ...


@dataclass
class SequenceConditionItem(BaseSequenceItem, BaseConditionItem):
    """
    A sequence containing only condition items.

    Suitable for use as an action item's termination_check.

    The condition function evaluates to "True" if every child's condition item
    also evaluates to "True".

    When not used as a termination_check, this behaves exactly
    like a normal Sequence Item.
    """
    children: List[BaseConditionItem] = field(default_factory=list)

    def get_condition_function(self) -> Evaluatable:
        child_funcs = [item.get_condition_function() for item in self.children]

        def cond_func():
            """
            Minimize network hits by failing at first issue
            """
            ok = True
            for cf in child_funcs:
                ok = ok and cf()
                if not ok:
                    break
            return ok

        return cond_func


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
                value = caget(self.pv)  # double caget, this is uneeded as currently the comp_condition has caget baked in

                if comp_condition():
                    return py_trees.common.Status.SUCCESS
                logger.debug(f"{self.name}: Value is {value}")

                # specific caput logic to SetPVActionItem
                caput(self.pv, self.value)
                return py_trees.common.Status.RUNNING
            except Exception as ex:
                logger.warning(f"{self.name}: work failed: {ex}")
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

                logging.debug(f"(wf) {self.name}: Value is {value}")
                if comp_condition():
                    return py_trees.common.Status.SUCCESS

                # specific caput logic to IncPVActionItem
                caput(self.pv, value + self.increment)
                return py_trees.common.Status.RUNNING
            except Exception as ex:
                logger.warning(f"{self.name}: work failed: {ex}")
                return py_trees.common.Status.FAILURE

        comp_cond = self.termination_check.get_condition_function()

        node = ActionNode(
            name=self.name,
            work_func=work_func,
            completion_condition=comp_cond,
        )

        return node


@dataclass
class CheckAndDoItem(BaseItem):
    check: BaseConditionItem = field(default_factory=DummyConditionItem)
    do: Union[SetPVActionItem, IncPVActionItem] = field(default_factory=SetPVActionItem)

    def __post_init__(self):
        # Clearly indicate the intent for serialization
        # If termination check is the default default, create the dummy item instead
        if self.do.termination_check == DummyConditionItem():
            self.do.termination_check = UseCheckConditionItem(
                name=f"{self.do.name}_termination_check",
                description=f"Use parent's check node: {self.check.name}"
            )

    def get_tree(self) -> CheckAndDo:
        if isinstance(self.do.termination_check, UseCheckConditionItem):
            active_do = copy(self.do)
            active_do.termination_check = self.check
        else:
            active_do = self.do

        check_node = self.check.get_tree()
        do_node = active_do.get_tree()

        node = CheckAndDo(name=self.name, check=check_node, do=do_node)

        return node


@dataclass
class UseCheckConditionItem(BaseConditionItem):
    """
    Dummy item: indicates that check and do should use "check" as do's termination check.

    If used in any other context the tree will not be constructable.
    """
    ...
