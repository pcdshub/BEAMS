import operator
from dataclasses import dataclass, field, fields
from typing import Any, Optional

import py_trees
from py_trees.behaviours import (CheckBlackboardVariableValue,
                                 WaitForBlackboardVariableValue)
from py_trees.common import ComparisonExpression, Status

from beams.tree_config.base import BaseItem
from beams.tree_config.condition import ConditionOperator


# py_trees.behaviours Behaviour items
class PyTreesItem:
    def get_tree(self):
        cls = getattr(py_trees.behaviours, type(self).__name__.removesuffix('Item'))
        kwargs = {}
        for inst_field in fields(self):
            if inst_field.name in ('description',):
                continue
            kwargs[inst_field.name] = getattr(self, inst_field.name)

        return cls(**kwargs)


@dataclass
class SuccessItem(PyTreesItem, BaseItem):
    pass


@dataclass
class FailureItem(PyTreesItem, BaseItem):
    pass


@dataclass
class RunningItem(PyTreesItem, BaseItem):
    pass


@dataclass
class DummyItem(PyTreesItem, BaseItem):
    pass


@dataclass
class PeriodicItem(PyTreesItem, BaseItem):
    n: int = 1


@dataclass
class StatusQueueItem(PyTreesItem, BaseItem):
    queue: list[Status] = field(default_factory=list)
    eventually: Optional[Status] = None


@dataclass
class SuccessEveryNItem(PyTreesItem, BaseItem):
    n: int = 2


@dataclass
class TickCounterItem(PyTreesItem, BaseItem):
    duration: int = 5
    completion_status: Status = Status.SUCCESS


@dataclass
class BlackboardToStatusItem(PyTreesItem, BaseItem):
    variable_name: str = 'default_variable'


@dataclass
class CheckBlackboardVariableExistsItem(PyTreesItem, BaseItem):
    variable_name: str = 'default_variable'


@dataclass
class WaitForBlackboardVariableItem(PyTreesItem, BaseItem):
    variable_name: str = 'default_variable'


@dataclass
class UnsetBlackboardVariableItem(PyTreesItem, BaseItem):
    key: str = 'default_variable'


@dataclass
class SetBlackboardVariableItem(PyTreesItem, BaseItem):
    variable_name: str = 'default_variable'
    variable_value: Any = 1
    overwrite: bool = True


@dataclass
class PyTreesComparison:
    variable_name: str = ''
    value: Any = 1
    operator: ConditionOperator = ConditionOperator.equal


@dataclass
class CheckBlackboardVariableValueItem(BaseItem):
    check: PyTreesComparison = field(default_factory=PyTreesComparison)

    def get_tree(self):
        comp_exp = ComparisonExpression(
            variable=self.check.variable_name,
            value=self.check.value,
            operator=getattr(operator, self.check.operator.value)
        )
        return CheckBlackboardVariableValue(name=self.name, check=comp_exp)


@dataclass
class WaitForBlackboardVariableValueItem(BaseItem):
    check: PyTreesComparison = field(default_factory=PyTreesComparison)

    def get_tree(self):
        comp_exp = ComparisonExpression(
            variable=self.check.variable_name,
            value=self.check.value,
            operator=getattr(operator, self.check.operator.value)
        )
        return WaitForBlackboardVariableValue(name=self.name, check=comp_exp)


# Add items here if they should be made available in the GUI
_supported_items = [
    SuccessItem,
    FailureItem,
    RunningItem,
    DummyItem,
    PeriodicItem,
    StatusQueueItem,
    StatusQueueItem,
    SuccessEveryNItem,
    TickCounterItem,
    BlackboardToStatusItem,
    CheckBlackboardVariableExistsItem,
    WaitForBlackboardVariableItem,
    UnsetBlackboardVariableItem,
    SetBlackboardVariableItem,
    CheckBlackboardVariableValueItem,
    WaitForBlackboardVariableValueItem,
]
