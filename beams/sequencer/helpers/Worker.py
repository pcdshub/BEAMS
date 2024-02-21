import logging
from multiprocessing import Process, Value
import time

"""
* An base class for child classes whos main function is to support a work thread.
* Holds volatile `self.do_work` which is intended to handle kill signal
* Provides `start_work` and `stop_work` functions to spawn and stop work processes 
* Optional constructor arg `stop_func` to be executde on process termination before joining work process.
"""


class Worker():
  def __init__(self, proc_name, stop_func=None):
    self.do_work = Value('i', False)
    self.proc_name = proc_name
    self.work_proc = Process(target=self.work_func, name=self.proc_name)
    self.stop_func = stop_func

  def start_work(self):
    if (self.do_work.value):
      logging.error("Already working, not starting work")
      return
    self.do_work.value = True
    self.work_proc.start()
    logging.info(f"Starting work on: {self.work_proc.pid}")

  def stop_work(self):
    logging.info(f"Calling stop work on: {self.work_proc.pid}")
    if (not self.do_work.value):
      logging.error("Not working, not stopping work")
      return
    self.do_work.value = False
    if (self.stop_func is not None):
      self.stop_func()

    print("calling join")
    self.work_proc.join()
    print("joined")

  def work_func(self):
    '''
    Example of what a work func can look like
    while(self.do_work.value):
      print(f"hi: {self.do_work.value}")
      time.sleep(1)
    logging.info(f"Work thread: {self.work_proc.pid} exit")
    '''
    raise NotImplementedError("Implement a work function in the child class!")

  def set_work_func(self, work_func):
    self.work_func = work_func
    self.work_proc = Process(target=self.work_func, name=self.proc_name, args=(self,))


if __name__ == "__main__":
  logging.basicConfig(filename='logs/worker.log', encoding='utf-8', level=logging.DEBUG)
  logging.getLogger().addHandler(logging.StreamHandler())
  s = Worker()
  s.start_work()
  time.sleep(3)
  s.stop_work()
