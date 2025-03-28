import py_trees

from beams.tree_config.condition import AcknowledgeConditionItem


def test_acknowledge(bt_cleaner):
    ack_cond_node = AcknowledgeConditionItem(
        name="test ack node",
        permisible_user_list=["robert", "zach"]
    )

    root = ack_cond_node.get_tree()

    root.acknowledge_node("josh")

    i = 0
    while (root.status != py_trees.common.Status.SUCCESS and i < 2):
        for n in root.tick():
            i += 1
            print(n)

    assert (root.status == py_trees.common.Status.FAILURE)

    root.acknowledge_node("robert")
    i = 0
    while (root.status != py_trees.common.Status.SUCCESS and i < 2):
        for n in root.tick():
            i += 1
            print(n)

    assert (root.status == py_trees.common.Status.SUCCESS)
