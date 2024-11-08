import json
from pathlib import Path
from typing import Union

from apischema import deserialize, serialize
from py_trees.trees import BehaviourTree

# Note: we must load all submodules with configuration items up front
# If we do not, then they are not necessarily in the schema yet
import beams.tree_config.action  # noqa: F401
import beams.tree_config.composite  # noqa: F401
import beams.tree_config.condition  # noqa: F401
import beams.tree_config.idiom  # noqa: F401
import beams.tree_config.py_trees  # noqa: F401
from beams.tree_config.base import BaseItem, BehaviorTreeItem


def get_tree_from_path(path: Path) -> BehaviourTree:
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
