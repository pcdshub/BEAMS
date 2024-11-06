from itertools import combinations, combinations_with_replacement

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

from beams.tree_config.base import BaseItem
from beams.tree_config.py_trees import (BlackboardToStatusItem, CheckBlackboardVariableExistsItem,
                                        CheckBlackboardVariableValueItem, DummyItem, FailureItem,
                                        PeriodicItem, RunningItem, SetBlackboardVariableItem,
                                        StatusQueueItem, SuccessEveryNItem, SuccessItem,
                                        TickCounterItem, UnsetBlackboardVariableItem, 
                                        WaitForBlackboardVariableItem, WaitForBlackboardVariableValueItem)
from beams.tree_config.condition import (BaseConditionItem, DummyConditionItem, 
                                         BinaryConditionItem, ThresholdConditionItem)
from beams.tree_config.action import (IncPVActionItem, SetPVActionItem)
from beams.tree_config.composite import (ParallelItem,  SelectorItem,
                                         SequenceConditionItem, SequenceItem)

from beams.tree_config.idiom import (CheckAndDoItem, UseCheckConditionItem)
                              

ITEM_TO_BEHAVIOUR = [
    (ParallelItem, Parallel),
    (SelectorItem, Selector),
    (SequenceItem, Sequence),
    (SuccessItem, Success),
    (FailureItem, Failure),
    (RunningItem, Running),
    (DummyItem, Dummy),
    (DummyConditionItem, ConditionNode),
    (BinaryConditionItem, ConditionNode),
    (ThresholdConditionItem, ConditionNode),
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

NOT_IMPLEMENTED_BASE_ITEM = [
    (BaseConditionItem, ConditionNode),
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
    combos = [tuple(options)]
    for size in range(3):
        for variant in combinations(options, size + 1):
            combos.append(variant)
    for tuple_of_cls in combos:
        item = item_class(**{attr: [cls() for cls in tuple_of_cls]})
        ser = apischema.serialize(item_class, item)
        deser = apischema.deserialize(item_class, ser)
        assert item == deser


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


def test_check_and_do_item_no_termination_check():
    check = DummyConditionItem(name="dummy_check")
    do = SetPVActionItem(name="dummy_do")
    assert not isinstance(do.termination_check, UseCheckConditionItem)
    item = CheckAndDoItem(
        name="dummy_check_and_do",
        check=check,
        do=do,
    )
    assert isinstance(item.do.termination_check, UseCheckConditionItem)

    ser = apischema.serialize(CheckAndDoItem, item)
    deser = apischema.deserialize(CheckAndDoItem, ser)
    assert item == deser

    node = item.get_tree()
    check_condition = node.check.condition
    do_condition = node.do.completion_condition
    # These should both run a copy of the dummy success check
    assert check_condition()
    assert do_condition()

    check.result = False
    node = item.get_tree()
    check_condition = node.check.condition
    do_condition = node.do.completion_condition
    # These should both run a copy of the dummy fail check
    assert not check_condition()
    assert not do_condition()
