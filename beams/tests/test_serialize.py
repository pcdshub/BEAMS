from apischema import deserialize, serialize

from beams.tree_config.action import IncPVActionItem, SetPVActionItem
from beams.tree_config.base import BehaviorTreeItem
from beams.tree_config.composite import SequenceItem
from beams.tree_config.condition import BinaryConditionItem, ConditionOperator
from beams.tree_config.idiom import CheckAndDoItem
from beams.tree_config.value import EPICSValue, FixedValue


def test_serialize_check_and_do():
    # c_obj = load_config("config.json")
    cond_item = BinaryConditionItem(
        left_value=EPICSValue(pv_name="PERC:COMP"),
        right_value=FixedValue(value=100),
        operator=ConditionOperator.greater_equal
    )
    action_item = IncPVActionItem(
        pv="PERC:COMP",
        increment=10,
        termination_check=cond_item
    )
    cnd_item = CheckAndDoItem(name="self_test", check=cond_item, do=action_item)

    tree_item = BehaviorTreeItem(root=cnd_item)
    ser = serialize(BehaviorTreeItem, tree_item)
    deser = deserialize(BehaviorTreeItem, ser)

    assert deser == tree_item


def test_serialize_youre_a_father_now():
    """
    Build children check and dos
    """
    # insert reticule if ret is not found
    ce1 = BinaryConditionItem(
        left_value=EPICSValue(pv_name="RET:FOUND"),
        right_value=FixedValue(value=1),
        operator=ConditionOperator.equal)
    de1 = SetPVActionItem(pv="RET:FOUND", value=1, termination_check=ce1)
    eg1 = CheckAndDoItem(name="ret_find", check=ce1, do=de1)

    # acquire pixel to world frame transform
    ce2 = BinaryConditionItem(
        left_value=EPICSValue(pv_name="RET:INSERT"),
        right_value=FixedValue(value=1),
        operator=ConditionOperator.equal)
    de2 = SetPVActionItem(pv="RET:INSERT", value=1, termination_check=ce2)
    eg2 = CheckAndDoItem(name="ret_insert", check=ce2, do=de2)

    root_item = SequenceItem(children=[eg1, eg2])
    eg_root = BehaviorTreeItem(root=root_item)

    ser = serialize(BehaviorTreeItem, eg_root)

    eg_deser = deserialize(BehaviorTreeItem, ser)
    assert eg_root == eg_deser
