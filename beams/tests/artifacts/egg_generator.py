"""
Python representations of the json artifacts used in testing.
"""

import json
from pathlib import Path

import py_trees
from apischema import serialize

from beams.tree_config.action import IncPVActionItem, SetPVActionItem
from beams.tree_config.base import BehaviorTreeItem
from beams.tree_config.composite import SequenceItem
from beams.tree_config.condition import (BinaryConditionItem,
                                         BoundedConditionItem,
                                         ConditionOperator,
                                         AcknowledgeConditionItem)
from beams.tree_config.idiom import CheckAndDoItem
from beams.tree_config.utility_trees.wait_for_ack import WaitForAckNodeItem
from beams.tree_config.py_trees import (RunningItem, StatusQueueItem,
                                        SuccessItem)
from beams.tree_config.value import EPICSValue, FixedValue


# egg 1
def create_egg_1(write: bool = False):
    check = BinaryConditionItem(
        name="self_test_check",
        left_value=EPICSValue(pv_name="PERC:COMP"),
        right_value=FixedValue(value=100),
        operator=ConditionOperator.greater_equal)

    do = IncPVActionItem(
        name='self_test_do',
        loop_period_sec=0.01,
        pv="PERC:COMP",
        increment=10
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
    check_item_1 = BinaryConditionItem(name='ret_find_check',
                                       left_value=EPICSValue(pv_name='RET:FOUND'),
                                       right_value=FixedValue(value=1),
                                       operator=ConditionOperator.greater_equal)
    do_item_1 = SetPVActionItem(
        name='ret_find_do', pv='RET:FOUND', value=1, loop_period_sec=0.01
    )
    cnd_1 = CheckAndDoItem(name='ret_find', check=check_item_1, do=do_item_1)

    seq.children.append(cnd_1)

    # CheckAndDo2
    check2 = BinaryConditionItem(name="ret_insert_check",
                                 left_value=EPICSValue(pv_name="RET:INSERT"),
                                 right_value=FixedValue(value=1),
                                 operator=ConditionOperator.greater_equal)
    do2 = SetPVActionItem(
        name="ret_insert_do", pv="RET:INSERT", value=1,
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


# im2l0 test
def create_im2l0_test(write: bool = False):
    im2l0 = SequenceItem(name="IM2L0_checker_outer")
    check = BinaryConditionItem(
        name="check_reticule_state",
        left_value=EPICSValue(pv_name="IM2L0:XTES:MMS:STATE:GET_RBV", as_string=True),
        right_value=FixedValue(value="OUT"),
        operator=ConditionOperator.equal
    )
    do = SetPVActionItem(
        name="set_reticule_state_to_out",
        loop_period_sec=0.01,
        pv="IM2L0:XTES:MMS:STATE:GET_RBV",
        value="OUT",
    )
    cnd1 = CheckAndDoItem(name="reticle_state_out", check=check, do=do)

    check2 = BoundedConditionItem(
        name="check_zoom_motor",
        value=EPICSValue(pv_name="IM2L0:XTES:CLZ.RBV"),
        lower_bound=FixedValue(value=24.8),
        upper_bound=FixedValue(value=25.2),
    )
    do2 = SetPVActionItem(
        name="set_zoom_motor",
        loop_period_sec=0.01,
        pv="IM2L0:XTES:CLZ.RBV",
        value=25,
    )
    cnd2 = CheckAndDoItem(name="zoom_motor", check=check2, do=do2)

    check3 = BinaryConditionItem(
        name="check_focus_motor",
        left_value=EPICSValue(pv_name="IM2L0:XTES:CLF.RBV"),
        right_value=FixedValue(value=50),
        operator=ConditionOperator.equal
    )
    do3 = SetPVActionItem(
        name="set_focus_motor",
        loop_period_sec=0.01,
        pv="IM2L0:XTES:CLF.RBV",
        value=50,
    )
    cnd3 = CheckAndDoItem(name="focus_motor", check=check3, do=do3)

    im2l0.children = [cnd1, cnd2, cnd3]
    root_item = BehaviorTreeItem(root=im2l0)

    if write:
        with open(Path(__file__).parent / "im2l0_test.json", 'w') as fd:
            ser = serialize(BehaviorTreeItem, root_item)
            json.dump(ser, fd, indent=2)
            fd.write('\n')

    return root_item


def create_test_ack(write: bool = False):
    ack_cond_item = AcknowledgeConditionItem(
        name="test_ack_node",
        permisible_user_list=["silke", "barry"]
    )
    egg = WaitForAckNodeItem(ack_cond_item=ack_cond_item, wait_time_out=1)
    
    root_item = BehaviorTreeItem(root=egg)
    if write:
        with open(Path(__file__).parent / "wait_for_ack.json", 'w') as fd:
            ser = serialize(BehaviorTreeItem, root_item)
            json.dump(ser, fd, indent=2)
            fd.write('\n')

    return root_item


if __name__ == "__main__":
    create_egg_1(write=True)
    create_egg_2(write=True)
    create_eternal_guard(write=True)
    create_im2l0_test(write=True)
    create_test_ack(write=True)
