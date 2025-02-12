"""
Contains logic for 'threads' which need to tick behavior trees
"""
from __future__ import annotations

import logging
import os
import time
from ctypes import c_bool, c_char_p, c_uint
from functools import partial
from multiprocessing import Value
from pathlib import Path

from py_trees.console import read_single_keypress
from py_trees.display import unicode_blackboard, unicode_tree
from py_trees.trees import BehaviourTree
from py_trees.visitors import SnapshotVisitor

from beams.logging import LoggingVisitor
from beams.service.helpers.worker import Worker
from beams.service.remote_calls.behavior_tree_pb2 import (
    BehaviorTreeUpdateMessage, TickConfiguration, TickStatus)
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


'''one shot', will only ever load in one tree from file path '''


def run_from_file_tree_tick_work_func(
    filepath: str,
    tick_count: int,
    tick_delay: float,
    interactive: bool,
    show_node_status: bool,
    show_tree: bool,
    show_blackboard: bool,
):
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
    def __init__(self, tick_delay_ms: c_uint, tick_config: TickConfiguration):
        self.current_node = Value(c_char_p, b"")   # potentially best accesible through self.tree and not this....
        # Consitutes a TickConfigurationMessage
        self.tick_delay_ms = Value(c_uint, tick_delay_ms)
        self.tick_config = Value(c_uint, tick_config)  # don't forget protobuf enums are just int wrappers
        # Control Flow Variables of Should I and How Should I tick this tree
        self.tick_current_tree = Value(c_bool, True)  # setting False will allow, stop_work / unloading
        self.pause_tree = Value(c_bool, True)  # start in paused state

    def get_node_name(self):
        return self.current_node.value.decode()

    def get_tick_config(self):
        return self.tick_config.value

    def get_tick_delay_ms(self):
        return self.tick_delay_ms.value

    def set_pause_tree(self, value):
        logger.debug(f"setting pause tree on thread: {os.getpid()}")
        self.pause_tree.value = value

    def get_pause_tree(self):
        logger.debug(f"checking pause tree on thread: {os.getpid()}")
        return self.pause_tree.value

    def get_tick_current_tree(self):
        return self.tick_current_tree.value

    def get_tick_interactive(self):
        return self.tick_config.value


class TreeTicker(Worker):
    def __init__(self, filepath: str,
                 init_tree_state: TreeState = None,
                 sync_man=None):
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
        self.sync_man = sync_man

    def shutdown(self):
        self.tree.shutdown()

    def get_tree_state(self):
        return self.state

    def update_tree_state(self, new_state: TreeState):
        self.state = new_state

    def get_behavior_tree_update(self) -> BehaviorTreeUpdateMessage:
        # translate py_trees enum right quick
        tick_state = dict(TickStatus.items())[self.tree.root.status.value]

        mess = BehaviorTreeUpdateMessage(
                mess_t=MessageType.MESSAGE_TYPE_BEHAVIOR_TREE_MESSAGE,
                tree_name=self.tree.root.name,  # again, atm nothing is strictly holding these in line
                tick_status=tick_state,
                node_name=self.state.get_node_name(),  # TOOD: josh figure out how we're going to pipe this...
                tick_config=self.state.get_tick_config(),
                tick_delay_ms=self.state.get_tick_delay_ms()
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

            while (self.state.get_tick_current_tree()):
                while (self.state.get_pause_tree()):
                    time.sleep(self.state.get_tick_delay_ms())  # reusing this here.... could use a semaphore...

                tick_tree(self.tree, self.state.get_tick_interactive() == TickConfiguration.INTERACTIVE, self.state.get_tick_delay_ms())

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
