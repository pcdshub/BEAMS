import py_trees

from beams.behavior_tree.ActionNode import ActionNode
from beams.behavior_tree.ConditionNode import ConditionNode


class CheckAndDo(py_trees.composites.Selector):
    def __init__(self, name: str, check: ConditionNode, do: ActionNode) -> None:
        super().__init__(name, memory=False)
        self.name = name
        self.check = check
        self.do = do
        self.add_children([check, do])
