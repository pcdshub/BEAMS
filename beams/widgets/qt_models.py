from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import IntEnum, auto
from typing import Any, Generator, Optional
from uuid import UUID

import qtawesome as qta
from py_trees.common import Status
from qtpy import QtCore

from beams.service.remote_calls.behavior_tree_pb2 import (NodeInfo, TickStatus,
                                                          TreeDetails)
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
    status: TickStatus = TickStatus.INVALID

    # Do these need to be renamed to deconflict qt methods?
    parent: Optional[QtBTreeItem] = None
    children: list[QtBTreeItem] = field(default_factory=list)

    def __post_init__(self):
        self._row = 0

    def update_from_tree_details(self, details: TreeDetails):
        """
        Update with information from tree_details (Status, uuid)
        fills uuids if dne, otherwise only fills if uuids match
        """
        def _inner_update(tree_item: QtBTreeItem, node_info: NodeInfo):
            if tree_item.node_id is None:
                tree_item.node_id = UUID(node_info.id.uuid)

            tree_item.status = getattr(Status, TickStatus.Name(node_info.status))

            if len(tree_item.children) != len(node_info.children):
                raise ValueError("Provided details do not match the tree being"
                                 "updated.")
            for item_c, node_c in zip(tree_item.children, node_info.children):
                _inner_update(item_c, node_c)

            return tree_item

        return _inner_update(self, details.node_info)

    @classmethod
    def from_behavior_tree_item(cls, tree: BehaviorTreeItem) -> QtBTreeItem:
        """convert from BehaviorTreeItem to QT-TreeItem"""
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

    # def refresh_tree(self) -> None:
    #     self.layoutAboutToBeChanged.emit()
    #     # self.root_item = build_tree(self.base_entry)
    #     self.layoutChanged.emit()

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
