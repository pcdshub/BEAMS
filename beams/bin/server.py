from multiprocessing import Manager

from beams.service.helpers.worker import Worker
from beams.service.server import SequenceServer
from beams.service.tree_ticker import TreeTicker

# toss arg parse here to start


class BeamsService(Worker):
  def __init__(self):
    self.syncman = Manager()

    self.tree_procs = self.syncman.dict()
    self.grpc_service = SequenceServer(self.tree_procs)

  def work_func(self):
    # the job of this work function will be to consume messages and update the managed trees
    while (self.do_work.value):
      pass


def kabosh():
  # start GRPC server
  grpc_server = SequenceServer()
  grpc_server.start_work()
  
  # start tree ticker
  tree_ticker = TreeTicker()
  tree_ticker.start_work()


def main(*args, **kwargs):
  kabosh()
