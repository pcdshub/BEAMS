from __future__ import annotations

import json
import logging
from copy import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union

import py_trees
from apischema import deserialize, serialize

from beams.behavior_tree.CheckAndDo import CheckAndDo
from beams.tree_config.action import IncPVActionItem, SetPVActionItem
from beams.tree_config.base import BaseItem, BehaviorTreeItem
from beams.tree_config.condition import BaseConditionItem, DummyConditionItem

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
