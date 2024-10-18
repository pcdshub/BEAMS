from __future__ import annotations

import json
import logging
import operator
from dataclasses import dataclass, field, fields
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional, Union

import py_trees
from apischema import deserialize, serialize
from epics import caget, caput
from py_trees.behaviour import Behaviour
from py_trees.behaviours import (CheckBlackboardVariableValue,
                                 WaitForBlackboardVariableValue)
from py_trees.common import ComparisonExpression, ParallelPolicy, Status
from py_trees.composites import Parallel, Selector, Sequence

from beams.behavior_tree.ActionNode import ActionNode, wrapped_action_work
from beams.behavior_tree.CheckAndDo import CheckAndDo
from beams.behavior_tree.ConditionNode import ConditionNode
from beams.serialization import as_tagged_union
from beams.typing_helper import Evaluatable

logger = logging.getLogger(__name__)


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


@dataclass
class BehaviorTreeItem:
    root: BaseItem

    def get_tree(self) -> py_trees.trees.BehaviourTree:
        return py_trees.trees.BehaviourTree(self.root.get_tree())


@as_tagged_union
@dataclass
class BaseItem:
    name: str = ""
    description: str = ""

    def get_tree(self) -> Behaviour:
        """Get the tree node that this dataclass represents"""
        raise NotImplementedError


@dataclass
class ExternalItem(BaseItem):
    path: str = ""

    def get_tree(self) -> Behaviour:
        # grab file
        # de-serialize tree, return it
        raise NotImplementedError


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


@dataclass
class SequenceItem(BaseItem):
    memory: bool = False
    children: List[BaseItem] = field(default_factory=list)

    def get_tree(self) -> Sequence:
        children = []
        for child in self.children:
            children.append(child.get_tree())

        node = Sequence(name=self.name, memory=self.memory, children=children)

        return node


# Custom LCLS-built Behaviors (idioms)
class ConditionOperator(Enum):
    equal = "eq"
    not_equal = "ne"
    less = "lt"
    greater = "gt"
    less_equal = "le"
    greater_equal = "ge"


@dataclass
class ConditionItem(BaseItem):
    pv: str = ""
    value: Any = 1
    operator: ConditionOperator = ConditionOperator.equal

    def get_tree(self) -> ConditionNode:
        cond_func = self.get_condition_function()
        return ConditionNode(self.name, cond_func)

    def get_condition_function(self) -> Evaluatable:
        op = getattr(operator, self.operator.value)

        def cond_func():
            # Note: this bakes EPICS into how Conditions work.
            # Further implictly now relies of type of "value" to determine whether to get as_string
            val = caget(self.pv, as_string=isinstance(self.value, str))
            if val is None:
                return False

            return op(val, self.value)

        return cond_func


@dataclass
class SetPVActionItem(BaseItem):
    pv: str = ""
    value: Any = 1
    loop_period_sec: float = 1.0

    termination_check: ConditionItem = field(default_factory=ConditionItem)

    def get_tree(self) -> ActionNode:

        @wrapped_action_work(self.loop_period_sec)
        def work_func(comp_condition: Evaluatable) -> py_trees.common.Status:
            try:
                # Set to running
                value = caget(self.pv)  # double caget, this is uneeded as currently the comp_condition has caget baked in

                if comp_condition():
                    return py_trees.common.Status.SUCCESS
                logger.debug(f"{self.name}: Value is {value}")

                # specific caput logic to SetPVActionItem
                caput(self.pv, self.value)
                return py_trees.common.Status.RUNNING
            except Exception as ex:
                logger.warning(f"{self.name}: work failed: {ex}")
                return py_trees.common.Status.FAILURE

        comp_cond = self.termination_check.get_condition_function()

        node = ActionNode(
            name=self.name,
            work_func=work_func,
            completion_condition=comp_cond,
        )

        return node


@dataclass
class IncPVActionItem(BaseItem):
    pv: str = ""
    increment: float = 1
    loop_period_sec: float = 1.0

    termination_check: ConditionItem = field(default_factory=ConditionItem)

    def get_tree(self) -> ActionNode:

        @wrapped_action_work(self.loop_period_sec)
        def work_func(comp_condition: Evaluatable) -> py_trees.common.Status:
            """
            To be run inside of a while loop
            Action node should take care of logging, reporting status
            """
            try:
                value = caget(self.pv)

                logging.debug(f"(wf) {self.name}: Value is {value}")
                if comp_condition():
                    return py_trees.common.Status.SUCCESS

                # specific caput logic to IncPVActionItem
                caput(self.pv, value + self.increment)
                return py_trees.common.Status.RUNNING
            except Exception as ex:
                logger.warning(f"{self.name}: work failed: {ex}")
                return py_trees.common.Status.FAILURE

        comp_cond = self.termination_check.get_condition_function()

        node = ActionNode(
            name=self.name,
            work_func=work_func,
            completion_condition=comp_cond,
        )

        return node


@dataclass
class CheckAndDoItem(BaseItem):
    check: ConditionItem = field(default_factory=ConditionItem)
    do: Union[SetPVActionItem, IncPVActionItem] = field(default_factory=SetPVActionItem)

    def get_tree(self) -> CheckAndDo:
        check_node = self.check.get_tree()
        do_node = self.do.get_tree()

        node = CheckAndDo(name=self.name, check=check_node, do=do_node)

        return node


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
