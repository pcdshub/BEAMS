import logging
import operator
from dataclasses import dataclass, field
from enum import Enum
from typing import List

from beams.behavior_tree.condition_node import AckConditionNode, ConditionNode
from beams.serialization import as_tagged_union
from beams.tree_config.base import BaseItem
from beams.tree_config.value import BaseValue, FixedValue
from beams.typing_helper import Evaluatable

logger = logging.getLogger(__name__)


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


class ConditionOperator(Enum):
    equal = "eq"
    not_equal = "ne"
    less = "lt"
    greater = "gt"
    less_equal = "le"
    greater_equal = "ge"


@dataclass
class BinaryConditionItem(BaseConditionItem):
    left_value: BaseValue = field(default_factory=lambda: FixedValue(0))
    right_value: BaseValue = field(default_factory=lambda: FixedValue(0))
    operator: ConditionOperator = ConditionOperator.equal

    def get_condition_function(self) -> Evaluatable:
        op = getattr(operator, self.operator.value)

        def cond_func():
            lhs = self.left_value.get_value()
            # TODO: determine if we want to do NULL handling should we get a value but it is None type
            rhs = self.right_value.get_value()

            eval = op(lhs, rhs)
            logger.debug(f"Evalling as lhs {lhs}, rhs {rhs}: {eval}")
            return eval

        return cond_func


@dataclass
class BoundedConditionItem(BaseConditionItem):
    # TODO: convinience members such as "symettric bounds", "relative tolerance", etc
    lower_bound: BaseValue = field(default_factory=lambda: FixedValue(0))
    upper_bound: BaseValue = field(default_factory=lambda: FixedValue(0))
    value: BaseValue = field(default_factory=lambda: FixedValue(0))

    def get_condition_function(self) -> Evaluatable:
        def cond_func():
            return self.lower_bound.get_value() < self.value.get_value() < self.upper_bound.get_value()

        return cond_func


@dataclass
class AcknowledgeConditionItem(BaseItem):
    permisible_user_list: List[str] = field(default_factory=list)
    unset_acknowledge_on_check: bool = True

    def get_tree(self) -> AckConditionNode:
        return AckConditionNode(self.name, self.permisible_user_list, self.unset_acknowledge_on_check)
