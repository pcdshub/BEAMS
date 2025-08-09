import pytest

from beams.service.remote_calls.behavior_tree_pb2 import (NodeId, NodeInfo,
                                                          TickStatus,
                                                          TreeDetails,
                                                          TreeStatus)
from beams.tests.conftest import ETERNAL_GUARD_PATH
from beams.tree_config import get_tree_item_from_path
from beams.tree_config.base import BehaviorTreeItem
from beams.widgets.qt_models import QtBTreeItem


@pytest.fixture
def eternal_guard_item() -> BehaviorTreeItem:
    return get_tree_item_from_path(ETERNAL_GUARD_PATH)


@pytest.fixture
def eternal_guard_details() -> TreeDetails:
    details = TreeDetails(
        tree_id=NodeId(
            name="eg",
            uuid="22e3fcf2-8635-477a-b50e-850931166f7b",
        ),
        node_info=NodeInfo(
            id=NodeId(
                name="Eternal Guard",
                uuid="56e4da1e-b3a9-4dc8-b27a-1c82cd0ba68d",
            ),
            status=TickStatus.RUNNING,
            children=[
                NodeInfo(
                    id=NodeId(
                        name="Condition 1",
                        uuid="05a83efd-6318-408f-9737-25f01d2d3090",
                    ),
                    status=TickStatus.SUCCESS,
                    children=[],
                ),
                NodeInfo(
                    id=NodeId(
                        name="Condition 2",
                        uuid="a33b309c-08cc-4922-a61d-bb3a4c799165",
                    ),
                    status=TickStatus.SUCCESS,
                    children=[],
                ),
                NodeInfo(
                    id=NodeId(
                        name="Task Sequence",
                        uuid="c201a150-b6f2-4afe-aa0a-4c52aa4a8a87",
                    ),
                    status=TickStatus.RUNNING,
                    children=[
                        NodeInfo(
                            id=NodeId(
                                name="Worker 1",
                                uuid="e8f2c943-fc22-4a3a-993a-c2f4c44f8651",
                            ),
                            status=TickStatus.SUCCESS,
                        ),
                        NodeInfo(
                            id=NodeId(
                                name="Worker 2",
                                uuid="2c654b9e-8659-444f-96ef-d9b20fec9c5f",
                            ),
                            status=TickStatus.RUNNING,
                        ),
                    ],
                ),
            ],
        ),
        tree_status=TreeStatus.TICKING,
    )
    return details


def assert_base_qtbtreeitem_info(tree_item: QtBTreeItem):
    # walks DFS
    for item, name, node_type in zip(
        tree_item.walk_tree(),
        ["<root>", "Eternal Guard", "Condition 1", "Condition 2", "Task Sequence",
         "Worker 1", "Worker 2"],
        ["", "Sequence", "StatusQueue", "StatusQueue", "Sequence", "Success",
         "Running"],
    ):
        assert item.name == name
        assert item.node_type == node_type


def test_create_qttreeitem(eternal_guard_item):
    tree_item = QtBTreeItem.from_behavior_tree_item(eternal_guard_item)
    assert tree_item.children[0].name == "Eternal Guard"

    for child, child_ct in zip(tree_item.children[0].children, [0, 0, 2]):
        assert len(child.children) == child_ct

    assert_base_qtbtreeitem_info(tree_item)


def test_update_qtitem_with_details(eternal_guard_item, eternal_guard_details):
    tree_item = QtBTreeItem.from_behavior_tree_item(eternal_guard_item)
    for item in tree_item.walk_tree():
        assert item.status is TickStatus.INVALID

    tree_item.update_from_tree_details(eternal_guard_details)

    assert tree_item.status == TreeStatus.TICKING
    for item in tree_item.walk_tree():
        assert item.status is not TickStatus.INVALID
        assert item.node_id is not None

    assert_base_qtbtreeitem_info(tree_item)
