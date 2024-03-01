import os
from multiprocessing import Queue, Event

from beams.sequencer.helpers.Worker import Worker
from beams.sequencer.SequencerState import SequencerState
from beams.sequencer.SequenceServer import SequenceServer


class Sequencer(Worker):
  def __init__(self):
    super().__init__("Sequencer")
    # state maintenece object
    self.state = SequencerState() 
    self.job_queue = Queue()
    self.job_ready = Event()

  """
  Parse messages into trees to be ticked.
  Insert into the relevant place in the job_queue, set job_ready event
  """
  def message_thread(self, worker_ref):
    print(f"{self.proc_name} running on pid: {os.getpid()}")
    while (self.do_work.value):
      self.sequence_server.message_ready_sem.acquire()
      request = self.sequence_server.message_queue.pop()
      print(request)
      # job = GenerateTreeFromRequest(request)

  """
  Spawn all needed workthreads:
  * GRPC Server
  * Message Handler
  Tick trees representing jobs to do in job_queue
  """
  def work_func(self):
    print(f"{self.proc_name} running on pid: {os.getpid()}")
    # GRPC server object
    self.sequence_server = SequenceServer(self.state)
    self.sequence_server.start_work()  # TODO: move to work thread
    # Message Handler thread
    self.message_worker = Worker("message_handler", work_func=self.message_thread)
    self.message_worker.start_work() 

    # Handle Work Queue
    while (self.do_work.value):
      self.job_ready.wait()
      job = self.job_queue.get()


if __name__ == "__main__":
  s = Sequencer()
  s.start_work()
