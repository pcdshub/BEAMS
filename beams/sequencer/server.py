import logging
import time
from concurrent import futures
from multiprocessing import Semaphore

import grpc

from beams.sequencer.helpers.queue import PriorityQueue
from beams.sequencer.helpers.worker import Worker
from beams.sequencer.remote_calls.sequencer_pb2 import (CommandReply,
                                                        MessageType)
from beams.sequencer.remote_calls.sequencer_pb2_grpc import (
    SequencerServicer, add_SequencerServicer_to_server)
from beams.sequencer.state import SequencerState

message_priority_dict = {
    MessageType.MESSAGE_TYPE_ALTER_RUN_STATE: 0,
    MessageType.MESSAGE_TYPE_ENQUEUE_SEQUENCE_PRIORITY: 1,
    MessageType.MESSAGE_TYPE_ENQUEUE_SEQUENCE: 2,
}


logger = logging.getLogger(__name__)


class SequenceServer(SequencerServicer, Worker):
    def __init__(self, sequencer_state):
        self.thread_pool = futures.ThreadPoolExecutor(max_workers=10)
        self.server = grpc.server(self.thread_pool)
        super().__init__("SequenceServer", lambda: self.server.stop(1))

        # in queue
        self.sequencer_state = sequencer_state
        # out queue
        self.message_queue = PriorityQueue(message_priority_dict)
        self.message_ready_sem = Semaphore(value=0)

    def EnqueueCommand(self, request, context):
        mess_t = request.mess_t
        if mess_t in message_priority_dict.keys():
            logger.debug(f"putting {request.seq_m.seq_t} of {mess_t} in queue")
            self.message_queue.put(request, mess_t)
            time.sleep(0.1)
            self.message_ready_sem.release()
        else:
            logger.error(
                f"Message type {mess_t} is not prioritized in sequence servers priority dictionary"
            )
            # TODO: return this info to client via command reply

        return CommandReply(**self.sequencer_state.get_command_reply())

    def RequestHeartBeat(self, request, context):
        return CommandReply(**self.sequencer_state.get_command_reply())

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
