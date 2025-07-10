"""
Contains logic for 'threads' which need to tick behavior trees
"""
from __future__ import annotations

import logging
import os
import time
from ctypes import c_bool, c_char_p, c_uint
from functools import partial
from multiprocessing import Semaphore, Value
from multiprocessing.managers import BaseManager
from pathlib import Path
from typing import Optional, Union
from uuid import UUID

from py_trees.common import Status
from py_trees.console import read_single_keypress
from py_trees.display import unicode_blackboard, unicode_tree
from py_trees.trees import BehaviourTree
from py_trees.visitors import SnapshotVisitor

from beams.behavior_tree.condition_node import AckConditionNode
from beams.logging import LoggingVisitor
from beams.service.helpers.worker import Worker
from beams.service.remote_calls.behavior_tree_pb2 import (
    BehaviorTreeUpdateMessage, NodeId, TickConfiguration, TickStatus,
    TreeStatus)
from beams.service.remote_calls.generic_message_pb2 import MessageType
from beams.tree_config import get_tree_from_path

logger = logging.getLogger(__name__)


def snapshot_post_tick_handler(
    snapshot_visitor: SnapshotVisitor,
    show_tree: bool,
    show_blackboard: bool,
    behaviour_tree: BehaviourTree,
) -> None:
    """
    Print data about the part of the tree visited.
    Does not log, to allow use of color codes.
    ``snapshot_visitor`` keeps track of visited nodes and their status

    Args:
        snapshot_handler: gather data about the part of the tree visited
        behaviour_tree: tree to gather data from
    """
    if show_tree:
        print(
            "\n"
            + unicode_tree(
                root=behaviour_tree.root,
                visited=snapshot_visitor.visited,
                previously_visited=snapshot_visitor.previously_visited,
                show_status=True
            )
        )

    if show_blackboard:
        print(unicode_blackboard())


def tick_tree(tree: BehaviourTree, interactive: bool, tick_delay: float):
    tree.tick()
    if interactive:
        read_single_keypress()
    else:
        time.sleep(tick_delay)


def run_from_file_tree_tick_work_func(
    filepath: str,
    tick_count: int,
    tick_delay: float,
    interactive: bool,
    show_node_status: bool,
    show_tree: bool,
    show_blackboard: bool,
):
    """one shot', will only ever load in one tree from file path"""
    logger.info(f"Running behavior tree at {filepath}")
    # grab config
    fp = Path(filepath).resolve()
    if not fp.is_file():
        raise ValueError("Provided filepath is not a file")

    tree = get_tree_from_path(fp)
    tree.visitors.append(LoggingVisitor(print_status=show_node_status))

    snapshot_visitor = SnapshotVisitor()
    tree.add_post_tick_handler(
        partial(snapshot_post_tick_handler,
                snapshot_visitor,
                show_tree,
                show_blackboard)
    )
    tree.setup()
    if tick_count <= 0:
        while True:
            try:
                tick_tree(tree, interactive, tick_delay)
            except KeyboardInterrupt:
                break
    else:
        for _ in range(tick_count):
            try:
                tick_tree(tree, interactive, tick_delay)
            except KeyboardInterrupt:
                break


class TreeState():
    def __init__(
        self,
        tick_delay_ms: int = 1000,
        tick_config: TickConfiguration = TickConfiguration.CONTINUOUS
    ):
        # Trees are ticked in worker subprocess, must pass relevant information
        # to the Ticker worker
        self.current_node = Value(c_char_p, b"")
        self.current_node_uuid = Value(c_char_p, b"")
        self.current_status = Value(c_char_p, b"INVALID")  # TickStatus enum name

        # Consitutes a TickConfigurationMessage
        self.tick_delay_ms = Value(c_uint, tick_delay_ms)
        # don't forget protobuf enums are just int wrappers
        self.tick_config = Value(c_uint, tick_config)

        # Control Flow Variables of Should I and How Should I tick this tree
        # setting False will allow, stop_work / unloading
        self.tick_current_tree = Value(c_bool, True)
        self.tree_status = Value(c_char_p, b"IDLE")  # start in paused state

    def get_node_name(self) -> Optional[NodeId]:
        """
        Returns the name of the node that ended the current tick.  This will
        be the "tip" of the tree, provided by py_trees
        """
        if ((self.current_node.value is not None) and
            (self.current_node_uuid.value is not None)):
            return NodeId(
                name=self.current_node.value.decode(),
                uuid=self.current_node_uuid.value.decode(),
            )

    def set_node_name(self, name: str, uuid: Union[UUID, str]) -> None:
        self.current_node.value = name.encode()
        self.current_node_uuid.value = str(uuid).encode()

    def get_root_status(self) -> TickStatus:
        status_name = getattr(self.current_status, "value", b"INVALID").decode()
        status = getattr(TickStatus, status_name)
        return status

    def set_root_status(self, status: Status) -> None:
        self.current_status.value = status.name.encode()

    def get_tick_config(self) -> TickConfiguration:
        return getattr(TickConfiguration, TickConfiguration.Name(self.tick_config.value))

    def get_tick_delay_ms(self) -> int:
        return int(self.tick_delay_ms.value)

    def get_tree_status(self) -> TreeStatus:
        tree_status_name = getattr(self.tree_status, "value", b"ERROR").decode()
        status = getattr(TreeStatus, tree_status_name)
        return status

    def set_tree_status(self, status: TreeStatus) -> None:
        self.tree_status.value = TreeStatus.Name(status).encode()

    def set_pause_tree(self, value: bool):
        logger.debug(f"setting pause tree on thread: {os.getpid()}")
        if value:
            self.set_tree_status(TreeStatus.IDLE)
        else:
            self.set_tree_status(TreeStatus.TICKING)

    def get_pause_tree(self) -> bool:
        logger.debug(f"checking pause tree on thread: {os.getpid()}")
        tree_status = self.get_tree_status()
        return tree_status == TreeStatus.IDLE

    def get_tick_current_tree(self) -> bool:
        return self.tick_current_tree.value


class TreeTicker(Worker):
    def __init__(self, filepath: str,
                 init_tree_state: Optional[TreeState] = None,
                 sync_man: Optional[BaseManager] = None):
        super().__init__("TreeTicker")
        self.fp = filepath

        # load new tree
        logger.info(f"Loading tree at {self.fp}")
        # grab config
        fp = Path(self.fp).resolve()
        if not fp.is_file():
            logging.error(f"Provided filepath: {self.fp} is not a file")
            raise ValueError("Provided filepath is not a file")

        self.tree = get_tree_from_path(fp)

        if init_tree_state is None:
            self.state = TreeState()
        else:
            self.state = init_tree_state

        # don't forget to null check this
        # This is currently not used.  Presumably we would need to expose
        # the port and address for clients to connect to this.
        self.sync_man = sync_man

        self.tick_sem = Semaphore(value=0)

    def shutdown(self):
        self.tree.shutdown()

    def get_tree_state(self):
        return self.state

    def update_tree_state(self, new_state: TreeState):
        self.state = new_state

    def get_behavior_tree_update(self) -> BehaviorTreeUpdateMessage:
        mess = BehaviorTreeUpdateMessage(
                mess_t=MessageType.MESSAGE_TYPE_BEHAVIOR_TREE_MESSAGE,
                tree_id=NodeId(name=self.tree.root.name,
                               uuid=str(self.tree.root.id)),
                tick_status=self.state.get_root_status(),
                node_id=self.state.get_node_name(),
                tick_config=self.state.get_tick_config(),
                tick_delay_ms=self.state.get_tick_delay_ms(),
                tree_status=self.state.get_tree_status(),
            )

        return mess

    def work_func(self):
        while (self.do_work.value):
            self.tree.visitors.append(LoggingVisitor(print_status=True))

            snapshot_visitor = SnapshotVisitor()
            self.tree.add_post_tick_handler(
                partial(snapshot_post_tick_handler,
                        snapshot_visitor,
                        True,
                        False)
            )
            try:
                while (self.state.get_tick_current_tree()):
                    while (self.state.get_pause_tree()):
                        # reusing this here.... could use a semaphore...
                        self.state.set_tree_status(TreeStatus.IDLE)
                        time.sleep(self.state.get_tick_delay_ms() / 1000)

                    # If we are in interactive mode
                    if self.state.get_tick_config() == TickConfiguration.INTERACTIVE:
                        # wait till the semaphore gets incremented, this is the IPC
                        # method to communicate a tick_interactive
                        got_tick = self.tick_sem.acquire(timeout=0.2)

                        # because of the timeout (makes cleaning up thread easier)
                        # we need to check how it timed out
                        if got_tick:
                            self.state.set_tree_status(TreeStatus.TICKING)
                            self.tree.tick()
                        else:
                            self.state.set_tree_status(TreeStatus.WAITING_ACK)
                    # otherwise we are in continous mode, tick the tree as normal!
                    else:
                        self.state.set_tree_status(TreeStatus.TICKING)
                        self.tree.tick()

                    # grab the last node before traversal reversal
                    self.state.set_node_name(
                        name=getattr(self.tree.tip(), "name", ""),
                        uuid=getattr(self.tree.tip(), "id", ""),
                    )
                    self.state.set_root_status(self.tree.root.status)
                    time.sleep(self.state.get_tick_delay_ms() / 1000)
            except Exception as ex:
                self.state.set_tree_status(TreeStatus.ERROR)
                logger.exception(ex)

    # Hooks for CommandMessages

    def start_tree(self):
        # if tree is in unpaused state throw error
        if (not self.state.get_pause_tree()):
            logging.error(f"Tree of name {self.tree.root.name} is already unpaused")
            return
        self.state.set_pause_tree(False)
        # NOTE: this was moved here as the os.getpid() of the owning Process object
        # was instantiated within the sync manager pid, this ensures we start()
        # from the same pid we created the object in. Is this flawless, no. Move at your own risk
        self.tree.setup()
        self.start_work()

    def pause_tree(self):
        # if tree is already paused log error
        if (self.state.get_pause_tree()):
            logging.error(f"Tree off name {self.tree.root.name} is already paused!!")
        self.state.set_pause_tree(True)
        logger.debug(f"Pausing tree of name {self.tree.root.name}")

    def command_tick(self):
        logger.debug(f"Tree: {self.tree.root.name} got command to tick")
        self.tick_sem.release()

    def acknowledge_node(self, node_name: str, user_name: str):
        logger.debug(f"Tree: {self.tree.root.name} got command to ack node: {node_name} from user: {user_name}")
        # find Node
        node = None
        # NOTE: (josh & zach) may well be a more effecient way to iterate through the tree
        for i in self.tree.root.iterate():
            # note this enumeration for very large trees may be spammy
            logger.debug(f"Checking against node: {i.name}")
            if (i.name == node_name and isinstance(i, AckConditionNode)):
                node = i
                node.acknowledge_node(user_name)
                logger.debug("Node found and acknowledged")
        if node is None:
            logger.error(f"Could not find node of name: {node_name} in tree: {self.tree.root.name}")
