import logging
from multiprocessing import Process, Value
import time
from VolatileStatus import VolatileStatus

def BTWorker(proc_name, work_func, stop_func=None):
  status = VolatileStatus()

  def work_function():
    work_proc = Process(target=work_func, name=proc_name, args=(status,))




  def __init__(self, proc_name, stop_func=None):
    self.do_work = Value('i', False)
    self.work_proc = Process(target=self.work_func, name=proc_name)
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
    if (self.stop_func != None):
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


if __name__ == "__main__":
  logging.basicConfig(filename='logs/worker.log', encoding='utf-8', level=logging.DEBUG)
  logging.getLogger().addHandler(logging.StreamHandler())
  s = Worker()
  s.start_work()
  time.sleep(3)
  s.stop_work()