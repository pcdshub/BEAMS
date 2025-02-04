"""
Contains logic for 'threads' which need to tick behavior trees
"""
from __future__ import annotations
import logging
import time
from ctypes import c_bool, c_char_p, c_uint
from dataclasses import dataclass
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


class TreeTicker(Worker):
    def __init__(self, filepath: str, init_tree_state: TreeTicker.TreeState = None):
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
            self.state = TreeTicker.TreeState()
        else:
            self.state = init_tree_state

    def get_tree_state(self):
        return self.state

    def update_tree_state(self, new_state: TreeTicker.TreeState):
        self.state = new_state

    @dataclass
    class TreeState():
        current_node : str = ""   # potentially best accesible through self.tree and not this....
        # Control Flow Variables of Should I and How Should I tick this tree
        tick_current_tree = True  # setting False will allow, stop_work / unloading
        pause_tree = True  # start in paused state
        # Consitutes a TickConfigurationMessage
        tick_delay_ms = 5
        tick_config = TickConfiguration.UNKNOWN  # don't forget protobuf enums are just int wrappers
        
        def __init__(self, tick_delay_ms: c_uint, tick_config: TickConfiguration):
            self.tick_delay_ms = tick_delay_ms
            self.tick_config = tick_config
            # self.current_node = ""
            # self.tick_current_tree = True
            # self.pause_tree = True
        
        # because I'm bad with @dataclass, and SyncManager.register only exposes "public", non __**__ functions these need public getters
        # TODO: someone smart do better, i feel like you can add __get__ to exposed...
        def get_node_name(self):
            return self.current_node
        
        def get_tick_config(self):
            return self.tick_config
        
        def get_tick_delay_ms(self):
            return self.tick_delay_ms

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
            self.state.tree.visitors.append(LoggingVisitor(print_status=True))

            snapshot_visitor = SnapshotVisitor()
            self.state.tree.add_post_tick_handler(
                partial(snapshot_post_tick_handler,
                        snapshot_visitor,
                        True,
                        False)
            )
            self.state.tree.setup()

            while (self.state.tick_current_tree.value):
                while (self.state.pause_tree.value):
                    time.sleep(self.state.tick_delay_ms.value)
                tick_tree(self.state.tree, self.state.tick_interactive.value, self.state.tick_delay_ms.value)
