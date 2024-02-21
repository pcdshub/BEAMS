import time
import os

from beams.sequencer.helpers.Worker import Worker
from beams.sequencer.SequencerState import SequencerState, SequencerStateVariable
from beams.sequencer.SequenceServer import SequenceServer


class Sequencer(Worker):
  def __init__(self):
    super().__init__("Sequencer")
    # state maintenece object
    self.state = SequencerState() 

  def message_thread(self, worker_ref):
    print(f"{self.proc_name} running on pid: {os.getpid()}")
    while (self.do_work.value):
      if (self.sequence_server.run_state_change_queue.qsize() != 0):
        mess = self.sequence_server.run_state_change_queue.get()
        self.state.set_value(SequencerStateVariable.RUN_STATE, mess.stateToUpdateTo)
      elif (self.sequence_server.sequence_request_queue.qsize() != 0):
        pass
      time.sleep(.1)

  def work_func(self):
    print(f"{self.proc_name} running on pid: {os.getpid()}")
    # GRPC server object
    self.sequence_server = SequenceServer(self.state)
    self.sequence_server.start_work()  # TODO: move to work thread
    # Message Handler thread
    self.message_worker = Worker("message_handler", work_func=self.message_thread)
    self.message_worker.start_work() 
    # spawn message handling thread
    pass


if __name__ == "__main__":
  s = Sequencer()
  s.start_work()
