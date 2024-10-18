import apischema
import pytest
from py_trees.behaviour import Behaviour
from py_trees.behaviours import (BlackboardToStatus,
                                 CheckBlackboardVariableExists,
                                 CheckBlackboardVariableValue, Dummy, Failure,
                                 Periodic, Running, SetBlackboardVariable,
                                 StatusQueue, Success, SuccessEveryN,
                                 TickCounter, UnsetBlackboardVariable,
                                 WaitForBlackboardVariable,
                                 WaitForBlackboardVariableValue)
from py_trees.composites import Parallel, Selector, Sequence

from beams.behavior_tree.ActionNode import ActionNode
from beams.behavior_tree.CheckAndDo import CheckAndDo
from beams.behavior_tree.ConditionNode import ConditionNode
from beams.tree_config import (BaseItem, BlackboardToStatusItem,
                               CheckAndDoItem,
                               CheckBlackboardVariableExistsItem,
                               CheckBlackboardVariableValueItem, ConditionItem,
                               DummyItem, FailureItem, IncPVActionItem,
                               ParallelItem, PeriodicItem, RunningItem,
                               SelectorItem, SequenceConditionItem,
                               SequenceItem, SetBlackboardVariableItem,
                               SetPVActionItem, StatusQueueItem,
                               SuccessEveryNItem, SuccessItem, TickCounterItem,
                               UnsetBlackboardVariableItem,
                               WaitForBlackboardVariableItem,
                               WaitForBlackboardVariableValueItem)

ITEM_TO_BEHAVIOUR = [
    (ParallelItem, Parallel),
    (SelectorItem, Selector),
    (SequenceItem, Sequence),
    (SuccessItem, Success),
    (FailureItem, Failure),
    (RunningItem, Running),
    (DummyItem, Dummy),
    (ConditionItem, ConditionNode),
    (SequenceConditionItem, Sequence),
    (SetPVActionItem, ActionNode),
    (IncPVActionItem, ActionNode),
    (CheckAndDoItem, CheckAndDo),
    (PeriodicItem, Periodic),
    (StatusQueueItem, StatusQueue),
    (SuccessEveryNItem, SuccessEveryN),
    (TickCounterItem, TickCounter),
    (BlackboardToStatusItem, BlackboardToStatus),
    (CheckBlackboardVariableExistsItem, CheckBlackboardVariableExists),
    (WaitForBlackboardVariableItem, WaitForBlackboardVariable),
    (UnsetBlackboardVariableItem, UnsetBlackboardVariable),
    (SetBlackboardVariableItem, SetBlackboardVariable),
    (CheckBlackboardVariableValueItem, CheckBlackboardVariableValue),
    (WaitForBlackboardVariableValueItem, WaitForBlackboardVariableValue),
]


@pytest.mark.parametrize('item, node_type', ITEM_TO_BEHAVIOUR)
def test_get_tree(item: BaseItem, node_type: Behaviour):
    item_instance = item()
    assert isinstance(item_instance.get_tree(), node_type)


@pytest.mark.parametrize('item_class', [item[0] for item in ITEM_TO_BEHAVIOUR])
def test_item_serialize_roundtrip(item_class: BaseItem):
    item = item_class()
    ser = apischema.serialize(item_class, item)

    deser = apischema.deserialize(item_class, ser)

    assert item == deser
