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


def test_update_qtitem_with_details():
    return


def test_create_qttreeite(eternal_guard_item):
    tree_item = QtBTreeItem.from_behavior_tree_item(eternal_guard_item)
    assert tree_item.name == "Eternal Guard"
