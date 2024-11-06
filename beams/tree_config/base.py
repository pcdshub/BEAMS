from dataclasses import dataclass
from typing import Any

import py_trees
from epics import caget
from py_trees.behaviour import Behaviour

from beams.serialization import as_tagged_union


@as_tagged_union
@dataclass
class BaseItem:
    name: str = ""
    description: str = ""

    def get_tree(self) -> Behaviour:
        """Get the tree node that this dataclass represents"""
        raise NotImplementedError


@dataclass
class BehaviorTreeItem:
    root: BaseItem

    def get_tree(self) -> py_trees.trees.BehaviourTree:
        return py_trees.trees.BehaviourTree(self.root.get_tree())


@dataclass
class ExternalItem(BaseItem):
    path: str = ""

    def get_tree(self) -> Behaviour:
        # grab file
        # de-serialize tree, return it
        raise NotImplementedError


@as_tagged_union
@dataclass
class BaseValue:
    def get_value(self) -> Any:
        raise NotImplementedError


@dataclass
class FixedValue(BaseValue):
    value: Any

    def get_value(self) -> Any:
        return self.value


@dataclass
class EPICSValue(BaseValue):
    pv_name: str
    as_string: bool = False

    def get_value(self) -> Any:
        return caget(self.pv_name, as_string=self.as_string)


@dataclass
class OphydTarget(BaseValue):
    device_name: str
    component_path: list[str]
