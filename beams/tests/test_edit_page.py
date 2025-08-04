from pathlib import Path

import pytest
from pytestqt.qtbot import QtBot

from beams.tests.conftest import TEST_CONFIG_PATHS
from beams.tree_config import get_tree_item_from_path
from beams.widgets.edit import EditPage
from beams.widgets.qt_models import QtBTreeItem


@pytest.mark.parametrize("config_path,", TEST_CONFIG_PATHS)
def test_edit_open_configs(qtbot: QtBot, config_path: Path):
    tree_item = get_tree_item_from_path(config_path)
    epage = EditPage(tree=tree_item, full_path=config_path)
    print(config_path, epage.full_path)
    qtbot.add_widget(epage)
    assert epage.tree is not None

    # check nodes have been created
    assert len(epage.node_editor.scene.to_digraph().nodes) > 0

    # check tree has been created
    assert isinstance(epage.tree_model.root_item, QtBTreeItem)
    assert len(epage.tree_model.root_item.children) > 0

# TODO: save load roundtrip once our nodes properly take metadata from the config
# files
