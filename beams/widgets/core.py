"""
Core classes and helpers for Qt-based display GUIs.
"""
from pathlib import Path
from typing import ClassVar

from qtpy.QtWidgets import QVBoxLayout, QWidget
from qtpy.uic import loadUiType

BEAMS_SOURCE_PATH = Path(__file__).parent.parent


class DesignerDisplay:
    """Helper class for loading designer .ui files and adding logic."""
    filename: ClassVar[str]

    def __init_subclass__(cls):
        """Read the file when the class is created"""
        super().__init_subclass__()
        if cls.filename:
            cls.ui_form, _ = loadUiType(
                str(BEAMS_SOURCE_PATH / 'ui' / cls.filename)
            )
        else:
            cls.ui_form = None

    def __init__(self, *args, **kwargs):
        """Apply the file to this widget when the instance is created"""
        super().__init__(*args, **kwargs)
        if self.ui_form is not None:
            self.ui_form.setupUi(self, self)

    def retranslateUi(self, *args, **kwargs):
        """Required function for setupUi to work in __init__"""
        self.ui_form.retranslateUi(self, *args, **kwargs)

    def show_type_hints(self):
        """Show type hints of widgets included in the display for development help."""
        cls_attrs = set()
        obj_attrs = set(dir(self))
        annotated = set(self.__annotations__)
        for cls in type(self).mro():
            cls_attrs |= set(dir(cls))
        likely_from_ui = obj_attrs - cls_attrs - annotated
        for attr in sorted(likely_from_ui):
            try:
                obj = getattr(self, attr, None)
            except Exception:
                ...
            else:
                if obj is not None:
                    print(f"{attr}: {obj.__class__.__module__}.{obj.__class__.__name__}")


def insert_widget(widget: QWidget, placeholder: QWidget) -> None:
    """
    Helper function for slotting e.g. data widgets into placeholders.
    """
    if placeholder.layout() is None:
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        placeholder.setLayout(layout)
    else:
        old_widget = placeholder.layout().takeAt(0).widget()
        if old_widget is not None:
            # old_widget.setParent(None)
            old_widget.deleteLater()
    placeholder.layout().addWidget(widget)
