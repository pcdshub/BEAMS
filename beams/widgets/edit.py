import logging
from pathlib import Path
from typing import Optional, Union

from qtpy import QtWidgets
from qtpynodeeditor import FlowView, PortType

from beams.tree_config.base import BehaviorTreeItem
from beams.widgets.core import DesignerDisplay, insert_widget
from beams.widgets.node_models import create_editor_view, tree_from_graph
from beams.widgets.qt_models import BehaviorTreeModel, QtBTreeItem

logger = logging.getLogger(__name__)


class EditPage(DesignerDisplay, QtWidgets.QWidget):
    filename = "edit_page.ui"

    tree_view: QtWidgets.QTreeView
    node_widget: QtWidgets.QWidget
    auto_arrange_button: QtWidgets.QPushButton
    update_tree_button: QtWidgets.QPushButton

    node_editor: FlowView
    tree: Optional[BehaviorTreeItem]

    def __init__(
        self,
        *args,
        tree: Optional[BehaviorTreeItem] = None,
        full_path: Optional[Union[Path, str]] = None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._setup_editor_widget()
        self._setup_callbacks()

        if tree is not None:
            self.load_tree(tree)
        else:
            self.tree = tree

        self.full_path = full_path

    def _setup_editor_widget(self) -> None:
        self.node_editor = create_editor_view()
        insert_widget(self.node_editor, self.node_widget)

    def _setup_callbacks(self) -> None:
        self.auto_arrange_button.clicked.connect(self.auto_arrange_nodes)
        self.update_tree_button.clicked.connect(self.update_tree_model)

    def update_tree_model(
        self,
        checked: bool = False,
        tree: Optional[BehaviorTreeItem] = None
    ) -> None:
        if tree is None or self.tree is None:
            digraph = self.node_editor.scene.to_digraph()
            self.tree = tree_from_graph(digraph)
        tree = self.tree
        # setup tree view
        self.tree_model = BehaviorTreeModel(
            tree=QtBTreeItem.from_behavior_tree_item(tree),
            show_status=False
        )
        self.tree_view.setModel(self.tree_model)
        self.tree_view.expandAll()

    def auto_arrange_nodes(self, *args, **kwargs) -> None:
        try:
            self.node_editor.scene.auto_arrange(layout="pygraphviz", prog="dot")
        except ImportError:
            logger.debug("pygraphviz not available to run auto arrange routine")

    def create_nodes_from_tree(self, tree: BehaviorTreeItem) -> None:
        """Create nodes and autoarrange the existing setup"""
        tree_item = QtBTreeItem.from_behavior_tree_item(tree)
        scene = self.node_editor.scene

        def _inner_create_node(tree_item: QtBTreeItem):
            if tree_item.node_type == "":
                model_name = " Root "  # TODO: deal with this spacing issue upstream
            else:
                model_name = tree_item.node_type
            model_cls = scene.registry.get_model_by_name(model_name)[0]
            node = scene.create_node(model_cls)

            for i, child in enumerate(tree_item.children):
                child_node = _inner_create_node(child)
                scene.create_connection(
                    node[PortType.output][i], child_node[PortType.input][0]
                )

            return node

        _ = _inner_create_node(tree_item)

        self.auto_arrange_nodes()

    def load_tree(self, tree: BehaviorTreeItem) -> None:
        """Load a tree"""
        self.tree = tree
        self.update_tree_model(tree=self.tree)
        self.create_nodes_from_tree(self.tree)
