import logging
from typing import Generator, List, Tuple

from qtpy import QtWidgets

from beams.widgets.core import DesignerDisplay, insert_widget
from beams.widgets.node_models import BeamsNode, create_editor_view

logger = logging.getLogger(__name__)


BFS_GENERATOR = Generator[Tuple[BeamsNode, List[BeamsNode]], None, None]


class EditPage(DesignerDisplay, QtWidgets.QWidget):
    filename = "edit_page.ui"

    tree_view: QtWidgets.QTreeView
    node_widget: QtWidgets.QWidget
    auto_arrange_button: QtWidgets.QPushButton

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_editor_widget()
        self._setup_callbacks()

    def _setup_editor_widget(self):
        self.node_editor = create_editor_view()
        insert_widget(self.node_editor, self.node_widget)

    def _setup_callbacks(self):
        self.auto_arrange_button.clicked.connect(self.auto_arrange_nodes)

    def auto_arrange_nodes(self, *args, **kwargs):
        try:
            self.node_editor.scene.auto_arrange(layout="pygraphviz", prog="dot")
        except ImportError:
            logger.debug("pygraphviz not available to run auto arrange routine")
