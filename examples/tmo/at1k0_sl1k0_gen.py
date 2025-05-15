import json
from pathlib import Path

import py_trees
from apischema import serialize

from beams.tree_config.action import IncPVActionItem, SetPVActionItem
from beams.tree_config.base import BehaviorTreeItem
from beams.tree_config.composite import SequenceItem, SelectorItem
from beams.tree_config.condition import (AcknowledgeConditionItem,
                                         BinaryConditionItem,
                                         BoundedConditionItem,
                                         ConditionOperator)
from beams.tree_config.idiom import CheckAndDoItem
from beams.tree_config.prebuilt.wait_for_ack import WaitForAckNodeItem
from beams.tree_config.value import EPICSValue, FixedValue


def create_at1k0_state_check_condition_node_item(state_int: int) -> BinaryConditionItem:
    return BinaryConditionItem(
              name="check_at1k0_case_1",
              left_value=EPICSValue(pv_name="AT1K0:GAS_MMA:01:Y:STATE:GET_RBV"),
              right_value=FixedValue(value=state_int),
              operator=ConditionOperator.equal
           )


def create_action_needed_on_sl1k0_based_on_state_item(x_value: float, y_value: float) -> SequenceItem:
    # check if SL1k0 in case 1 needs attention
    s1lk0_case_1_check_x_and_y = SequenceItem("s1lk0_case_1_check_x")
    s1lk0_case_1_check_x = BinaryConditionItem(
        name="s1lk0_case_1_check_x",
        left_value=EPICSValue(pv_name="SL1K0:POWER:ACTUAL_XWIDTH_RBV"),
        right_value=FixedValue(value=x_value),
        operator=ConditionOperator.less
    )
    s1lk0_case_1_check_y = BinaryConditionItem(
        name="s1lk0_case_1_check_y",
        left_value=EPICSValue(pv_name="SL1K0:POWER:ACTUAL_YWIDTH_RBV"),
        right_value=FixedValue(value=y_value),
        operator=ConditionOperator.less
    )
    s1lk0_case_1_check_x_and_y.children = [s1lk0_case_1_check_x, s1lk0_case_1_check_y]
    return s1lk0_case_1_check_x_and_y


def create_should_do_action_or_warn_node(case_name: str, 
                                         x_value_check: float, 
                                         y_value_check: float,
                                         x_do_value: float) -> SelectorItem:
    # build right hand, action side of case 1 tree
    action_needed_on_sl1k0 = SelectorItem("action_needed_on_sl1k0")
    
    # first we want to check if sl1k0 is in the right state (no action needed)
    check_if_action_is_needed = create_action_needed_on_sl1k0_based_on_state_item(x_value=x_value_check, 
                                                                                  y_value=y_value_check)
    action_needed_on_sl1k0.children.append(check_if_action_is_needed)

    # next we want to prompt the user is we want to act automatically OR just post warning
    should_do_action_or_warn_case = SelectorItem(name=f"should_do_action_case_{case_name}")
    should_do_action = SequenceItem(name="should_do_action_or_warn")
    # build wait for action
    ack_cond_item = AcknowledgeConditionItem(
        name="test_ack_node",
        permisible_user_list=["tmoopr"]
    )

    wait_for_action_case_1 = WaitForAckNodeItem(ack_cond_item=ack_cond_item, wait_time_out=600)
    should_do_action.children.append(wait_for_action_case_1)
    action_needed_on_sl1k0.children.append(should_do_action)
    # build action for success case  # TODO: determine if Y value needed...
    do_open_sl1k0_x = SetPVActionItem(
        name="do_open_sl1k0_x",
        loop_period_sec=0.1,
        pv="[GET THIS PV]",  # TODO: need to get the PV from Tong
        value=25,
    )
    should_do_action.children.append(do_open_sl1k0_x)
    should_do_action_or_warn_case.children.append(should_do_action)

    # build out warn case should the action fail
    set_warning_pv_action = SetPVActionItem(
        name="set_warning_pv_case_1_sl1k0",
        loop_period_sec=0.1,
        pv="",  # TODO GET WARNING PV
        value=1,
    )
    should_do_action_or_warn_case.children.append(set_warning_pv_action)
    
    return should_do_action_or_warn_case


def create_sl1k0_at1k0_state_resolution(write: bool = False):
    sl1k0_root = SequenceItem(name="SL1K0 Root")

    # build first case
    case_1_root = SequenceItem(name="Case 1")
    # is AT1K0 in case 1
    check_at1k0_case_1 = create_at1k0_state_check_condition_node_item(state_int=1)
    case_1_root.children.append(check_at1k0_case_1)

    # build subtree that determines automate vs warn
    check_sl1k0_pos_and_if_automate_case_1 = create_should_do_action_or_warn_node(case_name="1",
                                                                                  x_value_check=2,
                                                                                  y_value_check=2,
                                                                                  x_do_value=25)  # TODO check that this number is real
    case_1_root.children.append(check_sl1k0_pos_and_if_automate_case_1)

    sl1k0_root.children.append(case_1_root)
    
    root_item = BehaviorTreeItem(root=sl1k0_root)
    if write:
        with open(Path(__file__).parent / "sl1k0_permis.json", 'w') as fd:
            ser = serialize(BehaviorTreeItem, root_item)
            json.dump(ser, fd, indent=2)
            fd.write('\n')

    return root_item


if __name__ == "__main__":
    create_sl1k0_at1k0_state_resolution(write=True)
