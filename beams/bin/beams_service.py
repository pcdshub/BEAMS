from multiprocessing import Manager

from beams.service.helpers.worker import Worker
from beams.service.rpc_handler import RPCHandler
from beams.service.tree_ticker import TreeTicker

# toss arg parse here to start


class BeamsService(Worker):
  def __init__(self):
    self.sync_man = Manager()

    self.tree_procs = self.syncman.dict()
    self.grpc_service = RPCHandler(sync_manager=self.sync_man,
                                   dictionary_of_trees=self.tree_procs)

  def work_func(self):
    # the job of this work function will be to consume messages and update the managed trees
    while (self.do_work.value):
      pass


def main(*args, **kwargs):
  BeamsService()
