from pathlib import Path
from typing import Optional, Union

from py_trees.trees import BehaviourTree
from qtpy.QtWidgets import QAction, QFileDialog, QMainWindow, QTabWidget

from beams.tree_config import get_tree_from_path
from beams.widgets.core import DesignerDisplay
from beams.widgets.edit import EditPage


class MainWindow(DesignerDisplay, QMainWindow):
    filename = "main_window.ui"

    tab_widget: QTabWidget

    action_open_file: QAction

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        edit_widget = EditPage()

        self.tab_widget.addTab(edit_widget, "edit")
        self.action_open_file.triggered.connect(self.open_file)

    def open_file(self, *args, filename: Optional[str] = None, **kwargs):
        """
        Open an existing file and create a new tab containing it.

        The parameters are open as to accept inputs from any signal.

        Parameters
        ----------
        filename : str, optional
            The name to save the file as. If omitted, a dialog will
            appear to prompt the user for a filepath.
        """
        if filename is None:
            filename, _ = QFileDialog.getOpenFileName(
                parent=self,
                caption='Select a config',
                filter='Json Files (*.json)',
            )
        if not filename:
            return

        tree_data = get_tree_from_path(Path(filename))

        self._new_tab(data=tree_data, filename=filename)

    def _new_tab(
        self,
        data: BehaviourTree,
        filename: Optional[Union[Path, str]] = None
    ) -> None:
        """
        Open a new tab, setting up the tree widgets and run toggle.

        Parameters
        ----------
        data : ConfigurationFile or ProcedureFile
            The data to populate the widgets with. This is typically
            loaded from a file but does not need to be.
        filename : str, optional
            The full path to the file the data was opened from, if
            applicable. This lets us keep track of which filename to
            save back to.
        """
        raise NotImplementedError
