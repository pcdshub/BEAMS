
__all__ = [
    "BlackboardToStatusItem",
    "CheckBlackboardVariableExistsItem",
    "CheckBlackboardVariableValueItem",
    "FailureItem", "PeriodicItem", "RunningItem",
    "SetBlackboardVariableItem",
    "StatusQueueItem",
    "SuccessEveryNItem",
    "SuccessItem", "FailureItem",
    "TickCounterItem",
    "UnsetBlackboardVariableItem",
    "WaitForBlackboardVariableItem",
    "WaitForBlackboardVariableValueItem",
    "DummyItem",
    "BaseItem",
    "BehaviorTreeItem",
    "ExternalItem",
    "Target",
    "PVTarget",
    "ValueTarget",
    "BaseConditionItem",
    "DummyConditionItem",
    "ConditionOperator",
    "BinaryConditionItem",
    "ThresholdConditionItem",
    "get_tree_from_path",
    "save_tree_item_to_path",
    "ParallelMode",
    "ParallelItem",
    "SelectorItem",
    "BaseSequenceItem",
    "SequenceItem",
    "SequenceConditionItem",
    "SetPVActionItem",
    "IncPVActionItem",
    "CheckAndDoItem",
    "UseCheckConditionItem",
    "IncPVActionItem",
    "SetPVActionItem",
    "ParallelMode",
    "ParallelItem",
    "SelectorItem",
    "BaseSequenceItem",
    "SequenceItem",
    "SequenceConditionItem"
]
from .action import IncPVActionItem, SetPVActionItem
from .base import (BaseItem, BehaviorTreeItem, ExternalItem, PVTarget, Target,
                   ValueTarget)
from .condition import (BaseConditionItem, BinaryConditionItem,
                        ConditionOperator, DummyConditionItem,
                        ThresholdConditionItem)
from .composite import (BaseSequenceItem, ParallelItem, ParallelMode,
                        SelectorItem, SequenceConditionItem, SequenceItem)
from .py_trees import (BlackboardToStatusItem,
                       CheckBlackboardVariableExistsItem,
                       CheckBlackboardVariableValueItem, DummyItem,
                       FailureItem, PeriodicItem, RunningItem,
                       SetBlackboardVariableItem, StatusQueueItem,
                       SuccessEveryNItem, SuccessItem, TickCounterItem,
                       UnsetBlackboardVariableItem,
                       WaitForBlackboardVariableItem,
                       WaitForBlackboardVariableValueItem)
from .idiom import (CheckAndDoItem, UseCheckConditionItem)


import json
from typing import Union
from pathlib import Path
from apischema import deserialize, serialize

import py_trees


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
