import os
from multiprocessing import Event
from queue import Queue
from threading import Thread
import time

import py_trees

from beams.sequencer.helpers.Worker import Worker
from beams.sequencer.SequencerState import SequencerState
from beams.sequencer.SequenceServer import SequenceServer

from beams.tree_generator.TreeGenerator import GenerateTreeFromRequest

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
  def message_thread(self):
    print(f"{self.proc_name} running on pid: {os.getpid()}")
    while (self.do_work.value):
      self.sequence_server.message_ready_sem.acquire()  # block untill we get something to work on
      request = self.sequence_server.message_queue.pop()
      print(request)
      job = GenerateTreeFromRequest(request)
      print(job)
      self.job_queue.put(job)
      self.job_ready.set()

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
    self.message_worker = Thread(name="message_handler", target=self.message_thread)
    self.message_worker.start() 

    # Handle Work Queue
    while (self.do_work.value):
      self.job_ready.wait()
      print("ready for job")
      # invoke the function build out the root of the tree
      job = self.job_queue.get()()
      print(f"SUCC GET job root status: {job.root.status}")
      while (job.root.status != py_trees.common.Status.SUCCESS and job.root.status != py_trees.common.Status.FAILURE): 
        for n in job.root.tick():
          print(f"ticking: {n}")
          time.sleep(0.5)
          print(f"status of tick: {n.status}")

      print(f"{job} done")

if __name__ == "__main__":
  s = Sequencer()
  s.start_work()
