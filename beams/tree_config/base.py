import logging
from dataclasses import dataclass

import py_trees
from py_trees.behaviour import Behaviour

from beams.serialization import as_tagged_union

logger = logging.getLogger(__name__)


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
