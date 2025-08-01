import logging
import os
from pathlib import Path
from typing import Optional, Union

from qtpy.QtWidgets import (QAction, QFileDialog, QMainWindow, QTabWidget,
                            QWidget)

from beams.tree_config import get_tree_item_from_path, save_tree_item_to_path
from beams.tree_config.base import BehaviorTreeItem
from beams.widgets.core import DesignerDisplay
from beams.widgets.edit import EditPage
from beams.widgets.exception import DefaultExceptionNotifier, install

logger = logging.getLogger(__name__)


class MainWindow(DesignerDisplay, QMainWindow):
    filename = "main_window.ui"
    user_default_filename = 'untitled'
    user_filename_ext = 'json'

    tab_widget: QTabWidget

    action_open_file: QAction
    action_save_file: QAction
    action_save_as: QAction

    action_open_from_service: QAction
    action_config_connnect: QAction

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        edit_widget = EditPage()

        self.tab_widget.addTab(edit_widget, "edit")
        self.action_open_file.triggered.connect(self.open_file)
        self.action_save_file.triggered.connect(self.save)
        self.action_save_as.triggered.connect(self.save_as)

        # Tab close enabled in designer, need to wire close action manually
        self.tab_widget.tabCloseRequested.connect(
            self.tab_widget.removeTab
        )

        # Exception handling: show a dialog to catch exceptions in main qt thread
        install(use_default_handler=False)
        self.exception_notifier = DefaultExceptionNotifier(main_parent=self)

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

        tree_data = get_tree_item_from_path(Path(filename))

        self._new_edit_tab(data=tree_data, filename=filename)

    def _new_edit_tab(
        self,
        data: BehaviorTreeItem,
        filename: Optional[Union[Path, str]] = None
    ) -> None:
        """
        Open a tree in new edit tab, setting up the tree widgets

        Parameters
        ----------
        data : BehaviorTreeItem
            The data to populate the widgets with. This is typically
            loaded from a file but does not need to be.
        filename : str, optional
            The full path to the file the data was opened from, if
            applicable. This lets us keep track of which filename to
            save back to.
        """
        widget = EditPage(tree=data, full_path=filename)
        self.tab_widget.addTab(widget, self.get_tab_name(filename))
        curr_idx = self.tab_widget.count() - 1
        self.tab_widget.setCurrentIndex(curr_idx)

    def get_tab_name(self, filename: Optional[Union[Path, str]] = None):
        """
        Get a standardized tab name from a filename.
        """
        if filename is None:
            filename = self.user_default_filename
        filename = str(filename)
        if '.' not in filename:
            filename = '.'.join((filename, self.user_filename_ext))
        return os.path.basename(filename)

    def get_current_page_widget(self) -> QWidget:
        """
        Return the DualTree widget for the current open tab.
        """
        return self.tab_widget.currentWidget()

    def save(self, *args, **kwargs):
        """
        Save the currently selected tab to the last used filename.

        Reverts back to save_as if no such filename exists.

        The parameters are open as to accept inputs from any signal.
        """
        current_widget = self.get_current_page_widget()
        if not isinstance(current_widget, EditPage):
            logger.debug("You must be editing a tree to save a tree")
            return
        self.save_as(filename=current_widget.full_path)

    def save_as(self, *args, filename: Optional[Union[Path, str]] = None, **kwargs):
        """
        Save the currently selected tab, to a specific filename.

        The parameters are open as to accept inputs from any signal.

        Parameters
        ----------
        filename : str, optional
            The name to save the file as. If omitted, a dialog will
            appear to prompt the user for a filepath.
        """
        current_widget = self.get_current_page_widget()

        if not isinstance(current_widget, EditPage):
            logger.debug("You must be editing a tree to save a tree.")
            return
        if current_widget.tree is None:
            logger.debug("No tree to save.")
            return

        if filename is None:
            filename, _ = QFileDialog.getSaveFileName(
                parent=self,
                caption='Save as',
                filter='Json Files (*.json)',
            )
        filename = str(filename)
        if not filename.endswith('.json'):
            filename += '.json'
        try:
            save_tree_item_to_path(filename, current_widget.tree.root)
        except OSError:
            logger.exception(f'Error saving file {filename}')
        else:
            self.set_current_tab_name(filename)
            current_widget.full_path = filename

    def set_current_tab_name(self, filename: str):
        """
        Set the title of the current tab based on the filename.
        """
        self.tab_widget.setTabText(
            self.tab_widget.currentIndex(),
            self.get_tab_name(filename),
        )
