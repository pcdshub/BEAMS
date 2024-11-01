"""
Python representations of the json artifacts used in testing.
"""

import json
from pathlib import Path

import py_trees
from apischema import serialize

from beams.tree_config import (BehaviorTreeItem, CheckAndDoItem, ConditionItem,
                               ConditionOperator, IncPVActionItem, RunningItem,
                               SequenceItem, SetPVActionItem, StatusQueueItem,
                               SuccessItem)


# egg 1
def create_egg_1(write: bool = False):
    check = ConditionItem(name="self_test_check", pv="PERC:COMP", value=100,
                          operator=ConditionOperator.greater_equal)
    do = IncPVActionItem(
        name='self_test_do', loop_period_sec=0.01, pv="PERC:COMP",
        increment=10, termination_check=ConditionItem(
            pv="PERC:COMP", value=100, operator=ConditionOperator.greater_equal
        )
    )
    cnd_test = CheckAndDoItem(name='self_test', check=check, do=do)

    root_item = BehaviorTreeItem(root=cnd_test)

    if write:
        with open(Path(__file__).parent / "eggs.json", 'w') as fd:
            ser = serialize(BehaviorTreeItem, root_item)
            json.dump(ser, fd, indent=2)
            fd.write('\n')

    return root_item


# egg 2
def create_egg_2(write: bool = False):
    seq = SequenceItem(name='fake_reticle')

    # Check and Do 1
    check_item_1 = ConditionItem(name='ret_find_check', pv='RET:FOUND', value=1,
                                 operator=ConditionOperator.greater_equal)
    do_item_1 = SetPVActionItem(
        name='ret_find_do', pv='RET:FOUND', value=1, loop_period_sec=0.01,
        termination_check=ConditionItem(
            pv="RET:FOUND", value=1, operator=ConditionOperator.greater_equal
        )
    )
    cnd_1 = CheckAndDoItem(name='ret_find', check=check_item_1, do=do_item_1)

    seq.children.append(cnd_1)

    # CheckAndDo2
    check2 = ConditionItem(pv="RET:INSERT", value=1,
                           operator=ConditionOperator.greater_equal)
    do2 = SetPVActionItem(
        pv="RET:INSERT", value=1,
        termination_check=ConditionItem(
            pv='RET:INSERT', value=1, operator=ConditionOperator.greater_equal
        )
    )
    cnd_2 = CheckAndDoItem(name='ret_insert', check=check2, do=do2)
    seq.children.append(cnd_2)

    root = BehaviorTreeItem(root=seq)

    if write:
        with open(Path(__file__).parent / "eggs2.json", 'w') as fd:
            ser = serialize(BehaviorTreeItem, root)
            json.dump(ser, fd, indent=2)
            fd.write('\n')

    return root


# Eternal guard
def create_eternal_guard(write: bool = False):
    eternal_guard = SequenceItem(name="Eternal Guard", memory=False)
    condition_one = StatusQueueItem(
        name="Condition 1",
        queue=[
            py_trees.common.Status.SUCCESS,
            py_trees.common.Status.FAILURE,
            py_trees.common.Status.SUCCESS,
        ],
        eventually=py_trees.common.Status.SUCCESS,
    )
    condition_two = StatusQueueItem(
        name="Condition 2",
        queue=[
            py_trees.common.Status.SUCCESS,
            py_trees.common.Status.SUCCESS,
            py_trees.common.Status.FAILURE,
        ],
        eventually=py_trees.common.Status.SUCCESS,
    )
    task_sequence = SequenceItem(name="Task Sequence", memory=True)
    task_one = SuccessItem(name="Worker 1")
    task_two = RunningItem(name="Worker 2")

    eternal_guard.children.extend([condition_one, condition_two, task_sequence])
    task_sequence.children.extend([task_one, task_two])

    root_item = BehaviorTreeItem(root=eternal_guard)

    if write:
        with open(Path(__file__).parent / "eternal_guard.json", 'w') as fd:
            ser = serialize(BehaviorTreeItem, root_item)
            json.dump(ser, fd, indent=2)
            fd.write('\n')

    return root_item


if __name__ == "__main__":
    create_egg_1(write=True)
    create_egg_2(write=True)
    create_eternal_guard(write=True)
