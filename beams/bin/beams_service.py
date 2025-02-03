import logging
from multiprocessing import Manager
import time

from beams.service.helpers.worker import Worker
from beams.service.rpc_handler import RPCHandler
from beams.service.tree_ticker import TreeTicker

logger = logging.getLogger(__name__)

# toss arg parse here to start


class BeamsService(Worker):
    def __init__(self):
        super().__init__("BeamsService")
        self.sync_man = Manager()

        self.tree_procs = self.sync_man.dict()

    def work_func(self):
        self.grpc_service = RPCHandler(sync_manager=self.sync_man,
                                       dictionary_of_trees=self.tree_procs)
        self.grpc_service.start_work()

        # the job of this work function will be to consume messages and update the managed trees
        while (self.do_work.value):
            try:
                got_message = self.grpc_service.command_ready_sem.acquire(timeout=1)  # block untill we get something to work on
                if got_message:
                    request = self.grpc_service.incoming_command_queue.get()
                    logger.debug(f"inbound request f{request}")
            except Exception as e:
                logger.debug(e)
        self.grpc_service.stop_work()


def main(*args, **kwargs):
    x = BeamsService()
    x.start_work()
    input("Press Enter to stop...")
    x.stop_work()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()
