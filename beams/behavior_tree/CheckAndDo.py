import py_trees
from beams.behavior_tree.ActionNode import ActionNode
from beams.behavior_tree.ConditionNode import ConditionNode


class CheckAndDo():
  def __init__(self, name: str,  check: ConditionNode, do: ActionNode) -> None:
    self.name = name
    self.root = py_trees.composites.Selector(self.name, memory=False)
    self.check = check
    self.do = do
    self.root.add_children([check, do])

  def setup(self):
    self.root.setup_with_descendants()
