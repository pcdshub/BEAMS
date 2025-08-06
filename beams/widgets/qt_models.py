"""
Qt models and items for use across the BEAMS GUI.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import IntEnum, auto
from typing import Any, Generator, Optional, Union
from uuid import UUID

import qtawesome as qta
from py_trees.common import Status
from qtpy import QtCore

from beams.service.remote_calls.behavior_tree_pb2 import (NodeInfo, TickStatus,
                                                          TreeDetails,
                                                          TreeStatus)
from beams.tree_config.base import BaseItem, BehaviorTreeItem

logger = logging.getLogger(__name__)


STATUS_ICON_MAP = {
    TickStatus.INVALID: "fa5s.minus-circle",
    TickStatus.SUCCESS: "fa5s.check-circle",
    TickStatus.RUNNING: "fa5s.running",
    TickStatus.FAILURE: "fa5s.times-circlde",
}


class TreeHeader(IntEnum):
    NAME = 0
    TYPE = auto()
    STATUS = auto()


@dataclass
class QtBTreeItem:
    """
    Qt oriented tree item.  Meant to display a behavior tree in a
    QTreeView, and also store the state of a tree.

    Will be used to store the history of a tree at a given tick.
    """
    name: str = ""
    node_id: Optional[UUID] = None
    node_type: str = ""
    status: Union[TickStatus, TreeStatus] = TickStatus.INVALID

    # Do these need to be renamed to deconflict qt methods?
    parent: Optional[QtBTreeItem] = None
    children: list[QtBTreeItem] = field(default_factory=list)

    def __post_init__(self):
        # internal tracker for own row under parent.
        # Gets updated by qt updated by add/remove children methods
        self._row = 0

    def update_from_tree_details(self, details: TreeDetails):
        """
        Update with information from tree_details (Status, uuid)

        This assumes that self is the top-level root node, with only one child.
        This method handles the root node and calls :py:meth:`~.update_from_node_info`.

        see:

        Parameters
        ----------
        details : TreeDetails
            Tree details as returned from the BEAMS RPC service

        Raises
        ------
        ValueError
            If the provided `details` object is invalid (improper type or not root)
        """
        if not isinstance(details, TreeDetails):
            raise ValueError("Provided details must be a `TreeDetails` object "
                             f"as provided by the BEAMS Service, not {type(details)}")

        if len(self.children) != 1:
            raise ValueError("Please call this method from the root QtBTreeItem")

        # Update the root node manually
        self.status = details.tree_status
        self.node_id = UUID(details.tree_id.uuid)

        return self.children[0].update_from_node_info(details.node_info)

    def update_from_node_info(self, node_info: NodeInfo):
        """
        Update this tree item from a node_info object.

        In contrast to :py:meth:`~.update_from_tree_details`, this must be
        called from a node that is not the root

        Parameters
        ----------
        node_info : NodeInfo
            The NodeInfo to update this QtBTreeItem with.  This comes from the
            BEAMS RPC Service as a child of the TreeDetails object

        Raises
        ------
        ValueError
            If the provided NodeInfo does not match the tree item being updated.
        """
        self.node_id = UUID(node_info.id.uuid)
        self.status = getattr(Status, TickStatus.Name(node_info.status))

        # This is the simplest check I could think of to verify the two tree
        # structures matched
        if len(self.children) != len(node_info.children):
            raise ValueError("Provided details do not match the tree being "
                             "updated.  (number of children mismatched)")
        if self.node_type != node_info.type:
            raise ValueError("Provided details do not match the tree being "
                             "updated.  Node types mismatch: "
                             f"{self.node_type} vs {node_info.type}")
        for item_c, node_c in zip(self.children, node_info.children):
            item_c.update_from_node_info(node_c)

    @classmethod
    def from_behavior_tree_item(cls, tree: BehaviorTreeItem) -> QtBTreeItem:
        """
        Convert from BehaviorTreeItem to QT-BehaviorTreeItem from.
        A `BehaviorTreeItem` is the deserialized BEAMS tree object.

        Parameters
        ----------
        tree : BehaviorTreeItem
            BehaviorTreeItem to create a QtBTreeItem from

        Returns
        -------
        QtBTreeItem
            _description_
        """
        def _inner_get_tree_item(tree: BaseItem) -> QtBTreeItem:
            item = QtBTreeItem(
                name=tree.name, node_type=type(tree).__name__.removesuffix("Item")
            )
            if hasattr(tree, "children"):
                children = [_inner_get_tree_item(child) for child in tree.children]
                for child in children:
                    item.addChild(child)

            return item

        tree_root_item = _inner_get_tree_item(tree.root)
        root_item = QtBTreeItem(name="<root>")
        root_item.addChild(tree_root_item)
        return root_item

    def data(self, column: int) -> Any:
        """
        Return the data for the requested column.
        Column 0: name
        Column 1: type
        Column 2: Status

        Parameters
        ----------
        column : int
            data column requested

        Returns
        -------
        Any
        """
        if column == TreeHeader.NAME:
            return self.name
        elif column == TreeHeader.TYPE:
            return self.node_type
        elif column == TreeHeader.STATUS:
            return TickStatus.Name(self.status)

    def columnCount(self) -> int:
        """Return the item's column count"""
        return 3

    def childCount(self) -> int:
        """Return the item's child count"""
        return len(self.children)

    def child(self, row: int) -> QtBTreeItem:
        """Return the item's child"""
        if row >= 0 and row < self.childCount():
            return self.children[row]

        raise ValueError(f"Requested index ({row}) does not exist "
                         f"({self.childCount()} children)")

    def addChild(self, child: QtBTreeItem) -> None:
        """
        Add a child to this item.

        Parameters
        ----------
        child : TreeItem
            Child TreeItem to add to this TreeItem
        """
        child.parent = self
        child._row = len(self.children)
        self.children.append(child)

    def get_children(self) -> Generator[QtBTreeItem, None, None]:
        """Yield this item's children"""
        yield from self.children

    def row(self) -> int:
        """Return the item's row under its parent"""
        return self._row

    def icon(self):
        """return icon for this item"""
        icon_id = STATUS_ICON_MAP.get(self.status)
        return qta.icon(icon_id)

    def walk_tree(
        self,
    ) -> Generator[QtBTreeItem, None, None]:
        """
        Walk the tree depth-first and yield each node.
        """
        yield self
        for child in self.get_children():
            yield from child.walk_tree()

    def get_child(self, uuid: UUID) -> Optional[QtBTreeItem]:
        """
        Return the child with `uuid` from this tree's descendants.  Returns
        `None` if a match cannot be found.
        """
        for item in self.walk_tree():
            if item.node_id == uuid:
                return item

        return None


class BehaviorTreeModel(QtCore.QAbstractItemModel):
    def __init__(
        self,
        *args,
        tree: QtBTreeItem,
        show_status: bool = True,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.root_item = tree
        self.headers = ['name', 'type', 'status']
        self.show_status = show_status

    def headerData(
        self,
        section: int,
        orientation: QtCore.Qt.Orientation,
        role: int
    ) -> Any:
        """
        Returns the header data for the model.
        Currently only displays horizontal header data

        Parameters
        ----------
        section : int
            section to provide header information for
        orientation : Qt.Orientation
            header orientation, Qt.Horizontal or Qt.Vertical
        role : int
            Qt role to provide header information for

        Returns
        -------
        Any
            requested header data
        """
        if role != QtCore.Qt.DisplayRole:
            return

        if orientation == QtCore.Qt.Horizontal:
            return self.headers[section]

    def index(
        self,
        row: int,
        column: int,
        parent: QtCore.QModelIndex = QtCore.QModelIndex()
    ) -> QtCore.QModelIndex:
        """
        Returns the index of the item in the model.

        In a tree view the rows are defined relative to parent item.  If an
        item is the first child under its parent, it will have row=0,
        regardless of the number of items in the tree.

        Parameters
        ----------
        row : int
            The row of the requested index.
        column : int
            The column of the requested index
        parent : QtCore.QModelIndex, optional
            The parent of the requested index, by default None

        Returns
        -------
        QtCore.QModelIndex
        """
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        parent_item = None
        if not parent or not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)

        # all else return invalid index
        return QtCore.QModelIndex()

    def index_from_item(self, item: QtBTreeItem) -> QtCore.QModelIndex:
        return self.createIndex(item.row(), 0, item)

    def parent(self, index: QtCore.QModelIndex) -> QtCore.QModelIndex:
        """

        Parameters
        ----------
        index : QtCore.QModelIndex
            item to retrieve parent of

        Returns
        -------
        QtCore.QModelIndex
            index of the parent item
        """
        if not index.isValid():
            return QtCore.QModelIndex()
        child: QtBTreeItem = index.internalPointer()
        if child is self.root_item:
            return QtCore.QModelIndex()
        parent = child.parent
        if parent in (self.root_item, None):
            return QtCore.QModelIndex()

        return self.createIndex(parent.row(), 0, parent)

    def rowCount(self, parent: QtCore.QModelIndex) -> int:
        """
        Called by tree view to determine number of children an item has.

        Parameters
        ----------
        parent : QtCore.QModelIndex
            index of the parent item being queried

        Returns
        -------
        int
            number of children ``parent`` has
        """
        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()
        return parent_item.childCount()

    def columnCount(self, parent: QtCore.QModelIndex) -> int:
        """
        Called by tree view to determine number of columns of data ``parent`` has

        Parameters
        ----------
        parent : QtCore.QModelIndex

        Returns
        -------
        int
            number of columns ``parent`` has
        """
        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        if self.show_status:
            return parent_item.columnCount()
        else:
            return parent_item.columnCount() - 1

    def data(self, index: QtCore.QModelIndex, role: int) -> Any:
        """
        Returns the data stored under the given ``role`` for the item
        referred to by the ``index``.  Uses and assumes ``EntryItem`` methods.

        Parameters
        ----------
        index : QtCore.QModelIndex
            index that identifies the portion of the model in question
        role : int
            the data role

        Returns
        -------
        Any
            The data to be displayed by the model
        """
        if not index.isValid():
            return None

        item: QtBTreeItem = index.internalPointer()  # Gives original TreeItem

        # special handling for node type alignment
        if (
            index.column() == 1
            and role == QtCore.Qt.TextAlignmentRole
        ):
            return QtCore.Qt.AlignLeft

        if role == QtCore.Qt.DisplayRole:
            return item.data(index.column())

        if (
            role == QtCore.Qt.DecorationRole
            and index.column() == 0
            and self.show_status
        ):
            return item.icon()

        return None
