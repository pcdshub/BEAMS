import logging
import time
from concurrent import futures
from multiprocessing import Semaphore, Process, Queue

import grpc

from beams.service.helpers.queue import PriorityQueue
from beams.service.helpers.worker import Worker

from beams.service.remote_calls.generic_message_pb2 import MessageType
from beams.service.remote_calls.heartbeat_pb2 import HeartbeatReply
from beams.service.remote_calls.command_pb2 import (CommandType, LoadNewTreeMessage, AckNodeMessage, ChangeTickConfigurationMessage, CommandMessage)


from beams.service.remote_calls.sequencer_pb2_grpc import (
    SequencerServicer, add_SequencerServicer_to_server)
from beams.service.state import SequencerState

from beams.service.tree_ticker import TreeTicker

logger = logging.getLogger(__name__)


class SequenceServer(SequencerServicer, Worker):
    def __init__(self, dictionary_of_trees: dict[str, TreeTicker]):
        self.thread_pool = futures.ThreadPoolExecutor(max_workers=10)
        self.server = grpc.server(self.thread_pool)
        super().__init__("SequenceServer", lambda: self.server.stop(1))

        # process safe dictionary given by BEAMSService so we can appropriately respond with heartbeat
        self.tree_dict = dictionary_of_trees
        # out queue
        self.message_queue = Queue()
        self.message_ready_sem = Semaphore(value=0)

    def EnqueueCommand(self, request, context):
        mess_t = request.mess_t
        if mess_t != MessageType.MESSAGE_TYPE_COMMAND_MESSAGE:
            logger.error("You seriously messed up, reevlauate your life choices")
        else:
            command_t = request.command_t
            if (command_t )

        return HeartbeatReply(**self.sequencer_state.get_command_reply())

    def RequestHeartBeat(self, request, context):
        
        
        return HeartbeatReply(**self.sequencer_state.get_command_reply())

    def work_func(self):
        logger.debug(f"{self.proc_name} running")
        port = "50051"
        add_SequencerServicer_to_server(self, self.server)
        self.server.add_insecure_port("[::]:" + port)
        self.server.start()
        logger.debug("Server started, listening on " + port)
        while self.do_work.value:
            time.sleep(0.1)
        logger.debug("SequenceServer work_func exitted")


if __name__ == "__main__":
    logging.basicConfig()
    p = SequenceServer(SequencerState())
    p.start_work()

    time.sleep(5)
    p.stop_work()
