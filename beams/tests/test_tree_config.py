from itertools import combinations_with_replacement

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
from beams.serialization import get_all_subclasses, is_tagged_union
from beams.tree_config import (BaseConditionItem, BaseItem,
                               BlackboardToStatusItem, CheckAndDoItem,
                               CheckBlackboardVariableExistsItem,
                               CheckBlackboardVariableValueItem, ConditionItem,
                               DummyConditionItem, DummyItem, FailureItem,
                               IncPVActionItem, ParallelItem, PeriodicItem,
                               RunningItem, SelectorItem,
                               SequenceConditionItem, SequenceItem,
                               SetBlackboardVariableItem, SetPVActionItem,
                               StatusQueueItem, SuccessEveryNItem, SuccessItem,
                               TickCounterItem, UnsetBlackboardVariableItem,
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
    (DummyConditionItem, ConditionNode),
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


@pytest.mark.parametrize('item_class, node_type', ITEM_TO_BEHAVIOUR)
def test_get_tree(item_class: type[BaseItem], node_type: type[Behaviour]):
    item_instance = item_class()
    assert isinstance(item_instance.get_tree(), node_type)


@pytest.mark.parametrize('item_class', [item[0] for item in ITEM_TO_BEHAVIOUR])
def test_item_serialize_roundtrip(item_class: type[BaseItem]):
    item = item_class()
    ser = apischema.serialize(item_class, item)

    deser = apischema.deserialize(item_class, ser)

    assert item == deser


@pytest.mark.parametrize(
    'item_class, attr, expand',
    [
        (SetPVActionItem, "termination_check", BaseConditionItem),
        (IncPVActionItem, "termination_check", BaseConditionItem),
        (CheckAndDoItem, "check", BaseConditionItem),
    ]
)
def test_item_serialize_roundtrip_union_singles(item_class: type[BaseItem], attr: str, expand: type[BaseItem]):
    count = 0
    for cls in get_all_subclasses(expand):
        if is_tagged_union(cls):
            continue
        item = item_class(**{attr: cls()})
        ser = apischema.serialize(item_class, item)
        deser = apischema.deserialize(item_class, ser)
        assert item == deser
        count += 1
    # If all subclasses skip assert item == deser, we should also have an error
    assert count > 0


@pytest.mark.parametrize(
    'item_class, attr, expand',
    [
        (ParallelItem, "children", BaseItem),
        (SelectorItem, "children", BaseItem),
        (SequenceItem, "children", BaseItem),
        (SequenceConditionItem, "children", BaseConditionItem),
    ]
)
def test_item_serailize_roundtrip_union_sublists(item_class: type[BaseItem], attr: str, expand: type[BaseItem]):
    options = [cls for cls in get_all_subclasses(expand) if not is_tagged_union(cls)]
    combinations = []
    for size in (1, 2):
        for variant in combinations_with_replacement(options, size):
            combinations.append(variant)
    count = 0
    for tuple_of_cls in combinations:
        item = item_class(**{attr: [cls() for cls in tuple_of_cls]})
        ser = apischema.serialize(item_class, item)
        deser = apischema.deserialize(item_class, ser)
        assert item == deser
        count += 1
    # If all subclasses skip assert item == deser, we should also have an error
    assert count > 0


def test_sequence_condition_item_condition_function():
    item = SequenceConditionItem(
        name="mega_dummy",
        children=[
            DummyConditionItem(),
            DummyConditionItem(),
            DummyConditionItem(),
        ]
    )
    cond_func = item.get_condition_function()
    for variant in combinations_with_replacement((True, False), 3):
        for idx in range(3):
            item.children[idx].result = variant[idx]
        assert cond_func() == all(variant)
