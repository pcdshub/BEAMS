# toss arg parse here to start
import logging
import os
import sys
import time
from multiprocessing.managers import BaseManager

from beams.logging import setup_logging
from beams.service.helpers.worker import Worker
from beams.service.remote_calls.command_pb2 import CommandType
from beams.service.rpc_handler import RPCHandler
from beams.service.tree_ticker import TreeState, TreeTicker

logger = logging.getLogger(__name__)


class BeamsService(Worker):
    def __init__(self):
        super().__init__("BeamsService", grace_window_before_terminate_seconds=0.5)

        class SyncMan(BaseManager):
          pass

        # remote manager: https://docs.python.org/3/library/multiprocessing.html#using-a-remote-manager
        self.tree_dict = {}
        SyncMan.register("TreeTicker", TreeTicker)
        SyncMan.register("TreeState", TreeState)
        SyncMan.register("get_tree_dict", callable=lambda: self.tree_dict)

        self.sync_man = SyncMan()
        self.sync_man.start()
        logger.debug(f"Sync Man starting at: {self.sync_man.address}")

    def join_all_trees(self):
        with self.sync_man as man:
            tree_dict = man.get_tree_dict()
            for tree_name, tree in tree_dict.items():
              print(f"Cleaning up tree of name {tree_name}")
              tree.stop_work()
              tree.shutdown()

    def work_func(self):  # noqa: C901, sorry I want this standalone PR to be a good case study, will remove in next
        self.grpc_service = RPCHandler(sync_manager=self.sync_man)
        self.grpc_service.start_work()

        # the job of this work function will be to consume messages and update the managed trees
        while (self.do_work.value):
            try:
                got_message = self.grpc_service.command_ready_sem.acquire(timeout=0.2)  # block untill we get something to work on
                if got_message:
                    request = self.grpc_service.incoming_command_queue.get()
                    logger.debug(f"inbound command {request}")

                    if (request.command_t == CommandType.LOAD_NEW_TREE):
                        with self.sync_man as man:
                            tick_config_mess = request.load_new_tree.tick_spec
                            init_state = man.TreeState(
                                tick_delay_ms=tick_config_mess.delay_ms,
                                tick_config=tick_config_mess.tick_config
                                )
                            x = man.TreeTicker(filepath=request.load_new_tree.tree_file_path,
                                               init_tree_state=init_state)
                            tree_dict = man.get_tree_dict()
                            tree_dict.update({request.tree_name : x})
                            # self.tree_procs[request.tree_name].start_work()
                            logger.debug(f"Loaded tree of name {request.tree_name}" +
                                         f" from filepath: {request.load_new_tree.tree_file_path}" +
                                         " explciit START_TREE command will need to be issued for it to begin")
                    elif (request.command_t == CommandType.START_TREE):
                        with self.sync_man as man:
                            # get tree, again for now this is tree specified in json file,
                            # disambugiate this later
                            tree_name = request.tree_name
                            # get tree
                            tree_dict = man.get_tree_dict()
                            if (tree_name not in tree_dict.keys()):
                                logging.error(f"Error: {tree_name} is not in tree_dictionary: {tree_dict}")
                                continue
                            tree_to_start = tree_dict.get(tree_name)
                            tree_to_start.start_tree()
                    elif (request.command_t == CommandType.PAUSE_TREE):
                        with self.sync_man as man:
                            # get tree, again for now this is tree specified in json file,
                            # disambugiate this later
                            tree_name = request.tree_name
                            # get tree
                            tree_dict = man.get_tree_dict()
                            if (tree_name not in tree_dict.keys()):
                                logging.error(f"Error: {tree_name} is not in tree_dictionary: {tree_dict}")
                                continue
                            tree_to_start = tree_dict.get(tree_name)
                            tree_to_start.pause_tree()
                    elif (request.command_t == CommandType.TICK_TREE):
                        with self.sync_man as man:
                            # get tree, again for now this is tree specified in json file,
                            # disambugiate this later
                            tree_name = request.tree_name
                            # get tree
                            tree_dict = man.get_tree_dict()
                            if (tree_name not in tree_dict.keys()):
                                logging.error(f"Sorry fam {tree_name} is not in tree_dictionary: {tree_dict}")
                                continue
                            tree_to_start = tree_dict.get(tree_name)
                            tree_to_start.command_tick()

            except Exception as e:
                e_type, e_object, e_traceback = sys.exc_info()

                e_filename = os.path.split(
                    e_traceback.tb_frame.f_code.co_filename
                )[1]

                e_message = str(e)

                e_line_number = e_traceback.tb_lineno

                logger.exception(f'exception type: {e_type}')

                logger.exception(f'exception filename: {e_filename}')

                logger.exception(f'exception line number: {e_line_number}')

                logger.exception(f'exception message: {e_message}')
        self.grpc_service.stop_work()


def main(*args, **kwargs):
    x = BeamsService()
    x.start_work()

    while (input("press q to kill") != 'q'):
        time.sleep(1)
    x.join_all_trees()
    x.stop_work()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    setup_logging(logging.DEBUG)
    main()
