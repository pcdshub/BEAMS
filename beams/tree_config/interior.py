from enum import Enum
from dataclasses import dataclass, field
from typing import List

from py_trees.common import ParallelPolicy
from py_trees.composites import Parallel, Selector, Sequence

from beams.serialization import as_tagged_union
from beams.tree_config.base import BaseItem
from beams.tree_config.condition import BaseConditionItem
from beams.typing_helper import Evaluatable


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
