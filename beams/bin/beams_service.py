import sys
import os
import logging
import time
from multiprocessing.managers import BaseManager

from beams.service.helpers.worker import Worker
from beams.service.remote_calls.command_pb2 import CommandType
from beams.service.rpc_handler import RPCHandler
from beams.service.tree_ticker import TreeTicker

logger = logging.getLogger(__name__)


class BeamsService(Worker):
    def __init__(self):
        # TODO: make a singleton. Make process safe by leaving artifact file
        super().__init__("BeamsService", grace_window_before_terminate_seconds=0.5)

        # pattern inheritted:
        # remote manager: https://docs.python.org/3/library/multiprocessing.html#using-a-remote-manager
        class MyManager(BaseManager):
          pass

        self.tree_dict = {}
        MyManager.register("TreeTicker", TreeTicker)
        MyManager.register("TreeState", TreeTicker.TreeState)  # , exposed=('current_node', "tick_config", "tick_delay_ms")
        MyManager.register("get_tree_dict", callable=lambda: self.tree_dict)

        self.MyManager = MyManager()
        self.MyManager.start()
        logger.debug(f"Sync Man starting at: {self.MyManager.address}")

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
                          tick_config_mess = request.load_new_tree.tick_spec
                          init_state = man.TreeState(
                            tick_delay_ms=tick_config_mess.delay_ms,
                            tick_config=tick_config_mess.tick_config
                          )
                          x = man.TreeTicker(filepath=request.load_new_tree.tree_file_path,
                                             init_tree_state=init_state)
                          tree_dict = man.get_tree_dict()
                          tree_dict.update({request.tree_name : x})
                          logger.debug(f"Loaded tree of name {request.tree_name}" +
                                       f" from filepath: {request.load_new_tree.tree_file_path}" +
                                       " explciit START_TREE command will need to be issued for it to begin")

            except Exception as e:
                e_type, e_object, e_traceback = sys.exc_info()

                e_filename = os.path.split(
                    e_traceback.tb_frame.f_code.co_filename
                )[1]

                e_message = str(e)

                e_line_number = e_traceback.tb_lineno

                logger.error(f'exception type: {e_type}')

                logger.error(f'exception filename: {e_filename}')

                logger.error(f'exception line number: {e_line_number}')

                logger.error(f'exception message: {e_message}')
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
