import logging
from typing import Optional

from qtpy import QtWidgets
from qtpynodeeditor import FlowView

from beams.tree_config.base import BehaviorTreeItem
from beams.widgets.core import DesignerDisplay, insert_widget
from beams.widgets.node_models import create_editor_view, tree_from_graph
from beams.widgets.qt_models import BehaviorTreeModel

logger = logging.getLogger(__name__)


class EditPage(DesignerDisplay, QtWidgets.QWidget):
    filename = "edit_page.ui"

    tree_view: QtWidgets.QTreeView
    node_widget: QtWidgets.QWidget
    auto_arrange_button: QtWidgets.QPushButton

    node_editor: FlowView

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_editor_widget()
        self._setup_callbacks()
        self.update_tree_model()

    def _setup_editor_widget(self):
        self.node_editor = create_editor_view()
        insert_widget(self.node_editor, self.node_widget)

    def update_tree_model(self, tree: Optional[BehaviorTreeItem] = None):
        if tree is None:
            digraph = self.node_editor.scene.to_digraph()
            tree = tree_from_graph(digraph)
        # setup tree view
        self.tree_model = BehaviorTreeModel(tree=tree)
        self.tree_view.setModel(self.tree_model)

    def _setup_callbacks(self):
        self.auto_arrange_button.clicked.connect(self.auto_arrange_nodes)

    def auto_arrange_nodes(self, *args, **kwargs):
        try:
            self.node_editor.scene.auto_arrange(layout="pygraphviz", prog="dot")
        except ImportError:
            logger.debug("pygraphviz not available to run auto arrange routine")
