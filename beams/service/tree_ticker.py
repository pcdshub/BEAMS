"""
Contains logic for 'threads' which need to tick behavior trees
"""

import logging
import time
from functools import partial
from pathlib import Path
from multiprocessing import Value
from ctypese import c_char_p, c_bool, c_uint
from dataclasses import dataclass

from py_trees.console import read_single_keypress
from py_trees.display import unicode_blackboard, unicode_tree
from py_trees.trees import BehaviourTree
from py_trees.visitors import SnapshotVisitor

from beams.logging import LoggingVisitor
from beams.tree_config import get_tree_from_path
from beams.service.helpers.worker import Worker
from beams.service.helpers.enum import SharedEnum

from beams.service.remote_calls.generic_message_pb2 import MessageType
from beams.service.remote_calls.behavior_tree_pb2 import (TickStatus, TickConfiguration, BehaviorTreeUpdateMessage)

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
    def __init__(self):
        super().__init__("TreeTicker")
        self.state = TreeTicker.TreeState()

    @dataclass
    class TreeState():
        current_tree_fp = Value(c_char_p, b"")
        current_node = Value(c_char_p, b"")
        tick_current_tree = Value(c_bool, False)
        tick_delay_ms = Value(c_uint, 5)
        tick_interactive = Value(c_bool, False)
        pause_tree = Value(c_bool, False)
        tick_config = SharedEnum(TickConfiguration)
        tree: BehaviourTree

    def get_behavior_tree_update(self) -> BehaviorTreeUpdateMessage:
        mess = BehaviorTreeUpdateMessage(
                mess_t=MessageType.MESSAGE_TYPE_BEHAVIOR_TREE_MESSAGE,
                tree_name=self.state.current_tree_fp.value.decode(),
                node_name=self.state.current_node.value.decode(),
                tick_status=TickStatus.RUNNING,  # TOOD: josh actually plumb this up, next commit
                tick_config=self.tick_config.get_value(),
                tick_delay_ms=self.tick_delay_ms.value
            )

        return mess

    def work_func(self):
        while (self.do_work.value):
            # If filepath is available get file
            if self.state.current_tree_fp.value.decode() == "":
                time.sleep(100)
                continue
            else:
                # load new tree
                logger.info(f"Running behavior tree at {self.current_tree_fp.value.decode()}")
                # grab config
                fp = Path(self.current_tree_fp.value.decode()).resolve()
                if not fp.is_file():
                    raise ValueError("Provided filepath is not a file")

                self.state.tree = get_tree_from_path(fp)
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
