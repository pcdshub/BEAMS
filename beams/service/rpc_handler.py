import logging
import time
from concurrent import futures
from multiprocessing import Manager, Queue, Semaphore
from typing import Dict, List, Optional

import grpc

from beams.service.helpers.worker import Worker
from beams.service.remote_calls.beams_rpc_pb2_grpc import (
    BEAMS_rpcServicer, add_BEAMS_rpcServicer_to_server)
from beams.service.remote_calls.behavior_tree_pb2 import \
    BehaviorTreeUpdateMessage
from beams.service.remote_calls.generic_message_pb2 import MessageType
from beams.service.remote_calls.heartbeat_pb2 import HeartBeatReply
from beams.service.tree_ticker import TreeTicker

logger = logging.getLogger(__name__)


class RPCHandler(BEAMS_rpcServicer, Worker):
    def __init__(self, sync_manager: Manager, port=50051):
        # GRPC server launching things from docs:
        # https://grpc.io/docs/languages/python/basics/#starting-the-server
        self.thread_pool = futures.ThreadPoolExecutor(max_workers=10)
        self.server = grpc.server(self.thread_pool)
        self.server_port = port

        # calling Worker's super
        super().__init__(proc_name="RPCHandler",
                         stop_func=lambda: self.server.stop(1),
                         grace_window_before_terminate_seconds=.5)

        self.sync_man = sync_manager
        if sync_manager is not None:  # for testing modularity purposes
            # process safe dictionary given by BEAMSService so we can appropriately respond with heartbeat
            logger.debug(f"Connecting to sync_man at: {self.sync_man.address}")
            self.sync_man.connect()
            self.sync_man.register("get_tree_dict")
            self.sync_man.register("TreeTicker")
            self.sync_man.register("TreeState")

        # queue for owning object to grab commands s
        self.incoming_command_queue = Queue()
        self.command_ready_sem = Semaphore(value=0)

    # NOTE: these could also live and work in a process spawned by beams service..
    # returns a single bt update as a list...
    def attempt_to_get_tree_update(
        self, tree_name: str
    ) -> Optional[List[BehaviorTreeUpdateMessage]]:
        if self.sync_man is None:  # for testing modularity
            return None
        with self.sync_man as my_boy:
            tree_dict: Dict[str, TreeTicker] = my_boy.get_tree_dict()
            if tree_name in tree_dict.keys():
                return [tree_dict.get(tree_name).get_behavior_tree_update()]
            else:
                logger.error(f"Unable to find tree of name {tree_name} currently being ticked")
                return None

    def get_all_tree_updates(self) -> Optional[List[BehaviorTreeUpdateMessage]]:
        if self.sync_man is None:  # for testing modularity
            return None

        with self.sync_man as your_boy:
            tree_dict: Dict[str, TreeTicker] = your_boy.get_tree_dict()
            # if dictionary empty return none
            if len(tree_dict.items()) == 0:
                return None

            updates = [tree.get_behavior_tree_update() for tree in tree_dict.values()]

            return updates

    def enqueue_command(self, request, context) -> HeartBeatReply:
        mess_t = request.mess_t
        if mess_t != MessageType.MESSAGE_TYPE_COMMAND_MESSAGE:
            logger.error("You seriously messed up, reevlauate your life choices")
        else:
            self.incoming_command_queue.put(request)
            logger.debug(f"Command of type: {request.command_t} enqueued for {request.tree_name}")
            self.command_ready_sem.release()

        bt_update = None
        if self.sync_man is not None:  # for testing modularity
            bt_update = self.attempt_to_get_tree_update(request.tree_name)

        hbeat_message = HeartBeatReply(mess_t=MessageType.MESSAGE_TYPE_HEARTBEAT)
        hbeat_message.reply_timestamp.GetCurrentTime()

        if bt_update is None:
            return hbeat_message
        else:
            hbeat_message.behavior_tree_update.extend(bt_update)
            return hbeat_message

    def request_heartbeat(self, request, context) -> HeartBeatReply:
        # assumption that hitting this service endpoint means you want to know
        # ALL the trees this service is currently ticking

        # TODO: it is placing like here that I am not happy with the distance
        # of the py_trees vs GRPC object, reflect on this
        # for example: how could we keep thee py_tree treename and this one aligned?
        updates = self.get_all_tree_updates()

        hbeat_message = HeartBeatReply(mess_t=MessageType.MESSAGE_TYPE_HEARTBEAT)
        hbeat_message.reply_timestamp.GetCurrentTime()

        if updates is None:
            return hbeat_message
        else:
            hbeat_message.behavior_tree_update.extend(updates)
            return hbeat_message

    def work_func(self):
        logger.debug(f"{self.proc_name} running")
        add_BEAMS_rpcServicer_to_server(self, self.server)
        self.server.add_insecure_port(f"[::]:{self.server_port}")  # note: binding to localhost implicitly
        self.server.start()
        logger.debug("Server started, listening on " + str(self.server_port))
        while self.do_work.value:
            time.sleep(0.1)
        logger.debug("RPCHandler work_func exitted")
