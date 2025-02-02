import logging
import time
from concurrent import futures
from multiprocessing import Semaphore, Queue, Manager
from typing import Optional, List

import grpc
from google.protobuf.timestamp_pb2 import Timestamp


from beams.service.helpers.worker import Worker

from beams.service.remote_calls.generic_message_pb2 import MessageType
from beams.service.remote_calls.behavior_tree_pb2 import BehaviorTreeUpdateMessage
from beams.service.remote_calls.heartbeat_pb2 import HeartbeatReply


from beams.service.remote_calls.beams_rpc_pb2_grpc import (
    BEAMS_rpcServicer, add_BEAMS_rpcServicer_to_server)

from beams.service.tree_ticker import TreeTicker

logger = logging.getLogger(__name__)


class RPCHandler(BEAMS_rpcServicer, Worker):
    def __init__(self, sync_manager: Manager = Manager(), dictionary_of_trees: dict[str, TreeTicker] = dict()):
        # GRPC server launching things from docs: https://grpc.io/docs/languages/python/basics/#starting-the-server
        self.thread_pool = futures.ThreadPoolExecutor(max_workers=10)
        self.server = grpc.server(self.thread_pool)

        # calling Worker's super
        super().__init__("RPCHandler", lambda: self.server.stop(1))

        # process safe dictionary given by BEAMSService so we can appropriately respond with heartbeat
        self.sync_man = sync_manager
        self.tree_dict = dictionary_of_trees

        # queue for owning object to grab commands s
        self.incoming_command_queue = Queue()
        self.command_ready_sem = Semaphore(value=0)

    def attempt_to_get_tree_update(self, tree_name: str) -> Optional[BehaviorTreeUpdateMessage]:
        with self.sync_man:
            if tree_name in self.tree_dict:
                return self.tree_dict[tree_name].get_behavior_tree_update()
            else:
                logger.error(f"Unable to find tree of name {tree_name} currently being tickde")
                return None

    def get_all_tree_updates(self) -> List[BehaviorTreeUpdateMessage]:
        with self.sync_man:
            updates = [tree.get_behavior_tree_update() for tree in self.tree_dict.values()]
            return updates

    def EnqueueCommand(self, request, context) -> HeartbeatReply:
        mess_t = request.mess_t
        if mess_t != MessageType.MESSAGE_TYPE_COMMAND_MESSAGE:
            logger.error("You seriously messed up, reevlauate your life choices")
        else:
            self.incoming_command_queue.put(request)
            logger.debug(f"Command of type: {request.command_t} enqueued for {request.tree_name}")
            self.command_ready_sem.release()

        return HeartbeatReply(
                mess_t=MessageType.MESSAGE_TYPE_HEARTBEAT,
                reply_timestamp=Timestamp(),
                behavior_tree_update=[self.attempt_to_get_tree_update(request.tree_name)]
            )

    def RequestHeartBeat(self, request, context) -> HeartbeatReply:
        # assumption that hitting this service endpoint means you want to know ALL the trees this service is currently ticking

        # TODO: it is placing like here that I am not happy with the distance of the py_trees vs GRPC object, reflect on this
        # for example: how could we keep thee py_tree treename and this one aligned?
        return HeartbeatReply(
                mess_t=MessageType.MESSAGE_TYPE_HEARTBEAT,
                reply_timestamp=Timestamp(),
                behavior_tree_update=self.get_all_tree_updates()
            )

    def work_func(self):
        logger.debug(f"{self.proc_name} running")
        port = "50051"
        add_BEAMS_rpcServicer_to_server(self, self.server)
        self.server.add_insecure_port("[::]:" + port)
        self.server.start()
        logger.debug("Server started, listening on " + port)
        while self.do_work.value:
            time.sleep(0.1)
        logger.debug("RPCHandler work_func exitted")


if __name__ == "__main__":
    logging.basicConfig()
    p = RPCHandler()
    p.start_work()

    time.sleep(5)
    p.stop_work()
