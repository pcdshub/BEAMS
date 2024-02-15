from concurrent import futures
import logging
import time

from multiprocessing import Queue

import grpc

from beams.sequencer.helpers.Worker import Worker

from beams.sequencer.SequencerState import SequencerState
from beams.sequencer.remote_calls.sequencer_pb2_grpc import SequencerServicer, add_SequencerServicer_to_server
from beams.sequencer.remote_calls.sequencer_pb2 import CommandReply


class SequenceServer(SequencerServicer, Worker):
  def __init__(self, sequencer_state):
    self.thread_pool = futures.ThreadPoolExecutor(max_workers=10)
    self.server = grpc.server(self.thread_pool)
    super().__init__("SequenceServer", lambda: self.server.stop(1))

    # in queue
    self.sequencer_state = sequencer_state
    # out queue
    self.sequence_request_queue = Queue(maxsize=100) 
    self.run_state_change_queue = Queue(maxsize=100) 

  def EnqueueSequence(self, request, context):
    self.sequence_request_queue.put(request)
    return CommandReply(**self.sequencer_state.get_command_reply())

  def ChangeRunState(self, request, context):
    """Command a change in run paradigm of the program
    """
    self.run_state_change_queue.put(request)
    return CommandReply(**self.sequencer_state.get_command_reply())

  def RequestHeartBeat(self, request, context):
    return CommandReply(**self.sequencer_state.get_command_reply())

  def work_func(self):
      port = "50051"
      add_SequencerServicer_to_server(self, self.server)
      self.server.add_insecure_port("[::]:" + port)
      self.server.start()
      print("Server started, listening on " + port)
      while (self.do_work.value):
        time.sleep(1)
      print("exitted")


if __name__ == "__main__":
    logging.basicConfig()
    p = SequenceServer(SequencerState())
    p.start_work()

    time.sleep(5)
    p.stop_work()
