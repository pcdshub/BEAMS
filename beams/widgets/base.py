"""
Base class for embedded widgets and helper for gathering embedded widgets

Custom embedded widgets should be placed in submodules here with names matching
their item.

Example:

beams.tree_config.action.SetPVActionItem -> beams.widgets.action.SetPVActionWidget
"""

import importlib
from typing import Optional, Type

from qtpy import QtWidgets

from beams.tree_config.base import BaseItem


class EmbeddedNodeWidget(QtWidgets.QWidget):
    """
    Base class for a widget displayed inside a tree node.
    Should be a small widget, with very basic entry fields.

    Must implement the update_data for the corresponding dataclass
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def update_data(self, item: BaseItem) -> None:
        """
        Update `item` with information from this widget.
        To be implemented in the subclass
        """
        raise NotImplementedError


def get_embedded_widget(item_cls: Type[BaseItem]) -> Optional[Type[EmbeddedNodeWidget]]:
    """
    Get the embedded widget corresponding to `item_cls`.
    Search in the submodule of beams.widgets that matches the module `item_cls`
    is from for a widget with the same base name as `item_cls`

    Parameters
    ----------
    item_cls : Type[BaseItem]
        The item dataclass to find a widget for

    Returns
    -------
    Optional[Type[EmbeddedNodeWidget]]
        The corresponding widget, or None if one cannot be found
    """
    try:
        item_module_name = item_cls.__module__.split(".")[-1]
        item_base_name = item_cls.__name__.removesuffix("Item")
        mod = importlib.import_module(f"beams.widgets.{item_module_name}")
        widget = getattr(mod, f"{item_base_name}Widget")
    except (ModuleNotFoundError, AttributeError) as ex:
        print(ex)
        return

    return widget
