from __future__ import annotations

import json
import logging
from copy import copy
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Union

import py_trees
from apischema import deserialize, serialize

from py_trees.common import ParallelPolicy
from py_trees.composites import Parallel, Selector, Sequence

from beams.behavior_tree.CheckAndDo import CheckAndDo
from beams.serialization import as_tagged_union
from beams.tree_config.base import BaseItem, BehaviorTreeItem
from beams.tree_config.condition import BaseConditionItem, DummyConditionItem
from beams.tree_config.action import SetPVActionItem, IncPVActionItem
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
