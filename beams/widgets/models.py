"""
qtpynodeeditor data types for ui representations of Behavior Trees

These do not contain any logic related to actually ticking/running trees,
rather any connections that are made are only for validation and saving trees.

NodeData = edges
NodeDataModel = nodes
"""
import importlib
from typing import Optional, Sequence, Type

import qtpynodeeditor as nodeeditor
from qtpy.QtWidgets import QWidget
from qtpynodeeditor import (Connection, NodeData, NodeDataModel, NodeDataType,
                            NodeValidationState, Port)
from qtpynodeeditor.style import StyleCollection

from beams.tree_config import BaseItem
from beams.widgets.base import get_embedded_widget


class BlankNodeData(NodeData):
    """
    Node data with no caption.  We don't actually pass data between nodes,
    so there's no need to label the ports
    """
    # port caption defaults to node data type if there's no caption provided
    # add some spaces to help with spacing
    data_type = NodeDataType("n/a", "  ")


class RootNodeModel(NodeDataModel):
    """
    Root node model.  Simply holds one child node
    Is valid if it has a child
    """
    caption_visible = True
    num_ports = {"input": 0, "output": 1}
    port_caption_visible = {
        "input": {},
        "output": {0: False},
    }
    data_type = BlankNodeData.data_type
    name = " Root "

    def set_out_data(self, node_data: BlankNodeData, port: Port):
        # only validating that the parent node is a valid predecessor
        # self._parent_node = node_data.parent_node
        try:
            self._child_node = port.connections[0].output_node
            self._validation_state = NodeValidationState.valid
            self._validation_message = "Connected"
        except IndexError:
            self._validation_state = NodeValidationState.warning
            self._validation_message = "Uninitialized"


class MultiChildNodeModel(NodeDataModel):
    """
    Mixin class holding logic to enable dynamic number of children.
    This requires making .num_ports, .data_type, and .port_caption_visible
    react to the number of connections.

    num_ports is a property to avoid the validation performed by NodeDataModel

    Takes no children, and is valid if it has a parent
    """
    def __init__(self, style=None, parent=None, max_children: int = 0):
        super().__init__(style=style, parent=parent)
        self.caption_visible = True
        self.max_children = max_children
        # initial ports
        self._num_ports = {"input": 1, "output": 1}
        self._port_caption_visible = {
            "input": {0: False},
            "output": {0: False},
        }
        # for multiple ouptuts, must provide a dictionary
        # NodeDataModel tries to fill sensible default dictionaries, but gives up
        # if num_ports is a property (if dynamically defined)
        self._data_type = {
            "input": {0: BlankNodeData.data_type},
            "output": {0: BlankNodeData.data_type},
        }

        self._parent_node = None
        self._validation_state = NodeValidationState.warning
        self._validation_message = "Uninitialized"

        self.output_connections = []

    @property
    def caption(self):
        return self.name

    def validation_state(self) -> NodeValidationState:
        return self._validation_state

    def validation_message(self) -> str:
        return self._validation_message

    def set_in_data(self, node_data: BlankNodeData, port: Port):
        # only validating that the parent node is a valid predecessor
        # self._parent_node = node_data.parent_node
        try:
            self._parent_node = port.connections[0].input_node
            self._validation_state = NodeValidationState.valid
            self._validation_message = "Connected"
        except IndexError:
            self._validation_state = NodeValidationState.warning
            self._validation_message = "Uninitialized"

    @property
    def num_ports(self):
        return self._num_ports

    @property
    def data_type(self):
        return self._data_type

    @property
    def port_caption_visible(self):
        return self._port_caption_visible

    def output_connection_created(self, connection: Connection):
        # triggered from FlowScene when connection created.
        # want to add a new node
        if connection in self.output_connections:
            return
        self.output_connections.append(connection)
        self._update_output_info()

    def output_connection_deleted(self, connection):
        # need to take all existing connections and re-order them
        if connection not in self.output_connections:
            return
        self.output_connections.remove(connection)
        self._update_output_info()

    def _update_output_info(self):
        if self.max_children > 0:
            num_new_conn = min(len(self.output_connections) + 1,
                               self.max_children)
        else:
            num_new_conn = len(self.output_connections) + 1

        self._num_ports["output"] = num_new_conn
        self._port_caption_visible["output"] = {
            i: False for i in range(num_new_conn)
        }
        self._data_type["output"] = {
            i: BlankNodeData.data_type for i in range(num_new_conn)
        }


class LeafNodeModel(NodeDataModel):
    """
    NodeModel mixin for leaf nodes (action nodes)
    Takes no children, and is valid if it has a parent
    """
    caption_visible = True
    num_ports = {"input": 1, "output": 0}
    port_caption_visible = {
        "input": {0: False},
        "output": {}
    }
    data_type = BlankNodeData.data_type

    def __init__(self, style=None, parent=None):
        super().__init__(style=style, parent=parent)
        self._parent_node = None
        self._validation_state = NodeValidationState.warning
        self._validation_message = "Uninitialized"

    def __init_subclass__(cls, verify=True, **kwargs):
        return super().__init_subclass__(verify, **kwargs)

    @property
    def caption(self):
        return self.name

    def set_in_data(self, node_data: BlankNodeData, port: Port):
        # only validating that the parent node is a valid predecessor
        # self._parent_node = node_data.parent_node
        try:
            self._parent_node = port.connections[0].input_node
            self._validation_state = NodeValidationState.valid
            self._validation_message = "Connected"
        except IndexError:
            self._validation_state = NodeValidationState.warning
            self._validation_message = "Uninitialized"

    def validation_state(self) -> NodeValidationState:
        return self._validation_state

    def validation_message(self) -> str:
        return self._validation_message


class TreeNodeMixin:
    """
    Mixin that supplies functionality for storing behavior tree item
    objects and retrieving them.

    To be mixed in with a NodeModel of some sort... maybe?
    """
    item_cls: Type[BaseItem]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item = self.item_cls()
        self._widget_cls = get_embedded_widget(self.item_cls)
        if self._widget_cls:
            self._widget = self._widget_cls()
        else:
            self._widget = None

    def get_item(self):
        if self._widget:
            self._widget.update_data(self.item)
        return self.item

    def embedded_widget(self) -> Optional[QWidget]:
        """Fetch a QWidget"""
        return self._widget


def gather_models(submodule: str) -> Sequence[TreeNodeMixin]:
    """
    Gather and add all available models to the ``scene``
    Organize them by their submodule name
    """
    models = []
    mod = importlib.import_module(f"beams.tree_config.{submodule}")
    items = getattr(mod, "_supported_items")
    # Create a class mixing TreeNodeMixin + (appropiate Leaf/Parent)
    # also assign the right item class and name for the registry
    for item in items:
        name = str(item.__name__).removesuffix("Item")
        if hasattr(item(), "children"):
            node_model_cls = MultiChildNodeModel
        else:
            node_model_cls = LeafNodeModel

        model_cls = type(
            f"{name}Model", (TreeNodeMixin, node_model_cls),
            {"item_cls": item, "name": name})

        models.append(model_cls)

    return models


def add_items_to_registry(
    registry: nodeeditor.DataModelRegistry,
    style: StyleCollection,
    submodules: Optional[list[str]] = None,
):
    if submodules is None:
        submodules = ["action", "composite", "condition", "idiom", "py_trees",
                      "prebuilt"]

    for submod in submodules:
        models = gather_models(submod)
        for model in models:
            registry.register_model(model, category=submod, style=style)
