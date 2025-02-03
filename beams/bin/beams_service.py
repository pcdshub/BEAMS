import logging
import time
from multiprocessing.managers import BaseManager

from beams.service.helpers.worker import Worker
from beams.service.remote_calls.command_pb2 import CommandType
from beams.service.rpc_handler import RPCHandler
from beams.service.tree_ticker import TreeTicker

logger = logging.getLogger(__name__)

# toss arg parse here to start


class BeamsService(Worker):
    def __init__(self):
        super().__init__("BeamsService")

        class MyManager(BaseManager):
          pass

        # remote manager: https://docs.python.org/3/library/multiprocessing.html#using-a-remote-manager
        self.tree_dict = {}
        MyManager.register("TreeTicker", TreeTicker)
        MyManager.register("get_tree_dict", callable=lambda: self.tree_dict)

        self.MyManager = MyManager()
        logger.debug(f"Sync Man starting at: {self.MyManager.address}")
        self.MyManager.start()

    def work_func(self):
        self.grpc_service = RPCHandler(sync_manager=self.MyManager)
        self.grpc_service.start_work()

        # the job of this work function will be to consume messages and update the managed trees
        while (self.do_work.value):
            try:
                got_message = self.grpc_service.command_ready_sem.acquire(timeout=0.2)  # block untill we get something to work on
                if got_message:
                    request = self.grpc_service.incoming_command_queue.get()
                    logger.debug(f"inbound command {request}")

                    if (request.command_t == CommandType.LOAD_NEW_TREE):
                        with self.MyManager as man:
                          # relegated to user space to makesure the fil
                          logger.debug("got here")
                          x = man.TreeTicker(request.load_new_tree.tree_file_path)
                          logger.debug("what about here")
                          tree_dict = man.get_tree_dict()
                          tree_dict.update({request.tree_name : x})
                          logger.debug("not here")
                          # self.tree_procs[request.tree_name].start_work()
                          logger.debug(f"Loaded tree of name {request.tree_name}" +
                                       f" from filepath: {request.load_new_tree.tree_file_path}" +
                                       " explciit START_TREE command will need to be issued for it to begin")

            except Exception as e:
                logger.error(e)
        self.grpc_service.stop_work()


def main(*args, **kwargs):
    x = BeamsService()
    x.start_work()

    while (input("press q to kill") != 'q'):
      time.sleep(1)
    x.stop_work()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
