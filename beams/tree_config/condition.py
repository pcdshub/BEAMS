import operator
from dataclasses import dataclass, field
from enum import Enum

from beams.behavior_tree.ConditionNode import ConditionNode
from beams.serialization import as_tagged_union
from beams.tree_config.base import BaseItem, Target, ValueTarget
from beams.typing_helper import Evaluatable


@dataclass
class OphydTarget(Target):
    device_name: str
    component_path: list[str]


@as_tagged_union
@dataclass
class BaseConditionItem(BaseItem):
    def get_tree(self) -> ConditionNode:
        cond_func = self.get_condition_function()
        return ConditionNode(self.name, cond_func)

    def get_condition_function(self) -> Evaluatable:
        raise NotImplementedError


@dataclass
class DummyConditionItem(BaseConditionItem):
    result: bool = True

    def get_condition_function(self) -> Evaluatable:
        def cond_func():
            return self.result
        return cond_func


# Custom LCLS-built Behaviors (idioms)
class ConditionOperator(Enum):
    equal = "eq"
    not_equal = "ne"
    less = "lt"
    greater = "gt"
    less_equal = "le"
    greater_equal = "ge"


@dataclass
class BinaryConditionItem(BaseConditionItem):
    # pv: str = ""
    target: Target = field(default_factory=lambda: ValueTarget(0))
    target_value: Target = field(default_factory=lambda: ValueTarget(0))
    operator: ConditionOperator = ConditionOperator.equal

    def get_tree(self) -> ConditionNode:
        cond_func = self.get_condition_function()
        return ConditionNode(self.name, cond_func)

    def get_condition_function(self) -> Evaluatable:
        op = getattr(operator, self.operator.value)

        def cond_func():
            # val = caget(self.pv)
            # if val is None:
            #     return False
            val = self.target.get_value()

            tval = self.target_value.get_value()

            return op(val, tval)

        return cond_func


@dataclass
class RangeConditionThing(BaseConditionItem):
    llm: Target = field(default_factory=lambda: ValueTarget(0))
    hlm: Target = field(default_factory=lambda: ValueTarget(0))
    target: Target = field(default_factory=lambda: ValueTarget(0))

    def get_condition_function(self) -> Evaluatable:
        return self.llm < self.target.get_value() < self.hlm
