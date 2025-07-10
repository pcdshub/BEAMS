import logging
import time
from multiprocessing.managers import BaseManager
from typing import Callable, Dict

from beams.logging import setup_logging
from beams.service.helpers.worker import Worker
from beams.service.remote_calls.command_pb2 import CommandMessage, CommandType
from beams.service.rpc_handler import (RPCHandler, TreeIdKey,
                                       get_tree_from_treetickerdict)
from beams.service.tree_ticker import TreeState, TreeTicker

logger = logging.getLogger(__name__)

TreeTickerDict = Dict[TreeIdKey, TreeTicker]


class BeamsService(Worker):
    def __init__(self):
        # TODO: make a singleton. Make process safe by leaving artifact file
        super().__init__("BeamsService", grace_window_before_terminate_seconds=0.5)

        class SyncMan(BaseManager):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # For type hinting purposes only
                self.TreeTicker: type[TreeTicker]
                self.TreeState: type[TreeState]
                self.get_tree_dict: Callable[[], TreeTickerDict]

        self.tree_dict = {}
        SyncMan.register("TreeTicker", TreeTicker)
        SyncMan.register("TreeState", TreeState)
        SyncMan.register("get_tree_dict", callable=lambda: self.tree_dict)

        self.sync_man = SyncMan()
        self.sync_man.start()
        logger.debug(f"Sync Man starting at: {self.sync_man.address}")

    # mechanism to send shutdown signal to trees
    def join_all_trees(self):
        with self.sync_man as man:
            tree_dict = man.get_tree_dict()
            for tree_name, tree in tree_dict.items():
                logger.debug(f"Cleaning up tree of name {tree_name}")
                tree.stop_work()
                tree.shutdown()

    def work_func(self):
        self.grpc_service = RPCHandler(sync_manager=self.sync_man)
        self.grpc_service.start_work()

        # the job of this work function will be to consume messages and update
        # the managed trees
        while (self.do_work.value):
            try:
                # block untill we get something to work on
                if self.grpc_service.command_ready_sem.acquire(timeout=0.2):
                    request: CommandMessage = self.grpc_service.incoming_command_queue.get()
                    logger.debug(f"inbound command {request}")

                    if (request.command_t == CommandType.LOAD_NEW_TREE):
                        self.load_new_tree(request)
                    elif (request.command_t == CommandType.START_TREE):
                        self.start_tree(request)
                    elif (request.command_t == CommandType.PAUSE_TREE):
                        self.pause_tree(request)
                    elif (request.command_t == CommandType.TICK_TREE):
                        self.tick_tree(request)
                    elif (request.command_t == CommandType.ACK_NODE):
                        self.acknowledge_node(request)

            except Exception:
                logger.exception('Exception caught')
        self.grpc_service.stop_work()

    def load_new_tree(self, request: CommandMessage) -> None:
        with self.sync_man as man:
            tick_config_mess = request.load_new_tree.tick_spec
            init_state = man.TreeState(
                tick_delay_ms=tick_config_mess.delay_ms,
                tick_config=tick_config_mess.tick_config
            )
            x = man.TreeTicker(filepath=request.load_new_tree.tree_file_path,
                               init_tree_state=init_state)
            tree_dict = man.get_tree_dict()
            print(type(tree_dict))

            # New trees won't have uuids, but likely have names
            tree_id = TreeIdKey(name=request.tree_name)
            tree_dict.update({tree_id: x})
            logger.debug(f"Loaded tree ({request.tree_name}) from filepath: "
                         f"{request.load_new_tree.tree_file_path}.  Explcit "
                         "START_TREE command needed to begin ticking.")

    def start_tree(self, request: CommandMessage) -> None:
        with self.sync_man as man:
            # get tree
            tree_dict = man.get_tree_dict()
            tree_ticker = get_tree_from_treetickerdict(
                tree_dict, name=request.tree_name, uuid=request.tree_uuid,
            )
            if tree_ticker is not None:
                tree_ticker.start_tree()

    def pause_tree(self, request: CommandMessage) -> None:
        with self.sync_man as man:
            # get tree
            tree_dict = man.get_tree_dict()
            tree_ticker = get_tree_from_treetickerdict(
                tree_dict, name=request.tree_name, uuid=request.tree_uuid,
            )
            if tree_ticker is not None:
                tree_ticker.pause_tree()

    def tick_tree(self, request: CommandMessage) -> None:
        with self.sync_man as man:
            # get tree
            tree_dict = man.get_tree_dict()
            tree_ticker = get_tree_from_treetickerdict(
                tree_dict, name=request.tree_name, uuid=request.tree_uuid,
            )
            if tree_ticker is not None:
                tree_ticker.command_tick()

    def acknowledge_node(self, request: CommandMessage):
        node_name_to_ack = request.ack_node.node_name_to_ack
        user_acking_node = request.ack_node.user_acking_node
        with self.sync_man as man:
            tree_dict = man.get_tree_dict()
            tree_ticker = get_tree_from_treetickerdict(
                tree_dict, name=request.tree_name, uuid=request.tree_uuid,
            )
            if tree_ticker is not None:
                tree_ticker.acknowledge_node(
                    node_name_to_ack, user_acking_node
                )


def main(*args, **kwargs):
    service = BeamsService()
    service.start_work()

    while (input("press q+<enter> to kill") != 'q'):
        time.sleep(1)
    service.join_all_trees()
    service.stop_work()


if __name__ == "__main__":
    setup_logging(logging.DEBUG)
    main()
