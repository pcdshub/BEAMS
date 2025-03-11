# toss arg parse here to start
import logging
import time
from multiprocessing.managers import BaseManager

from beams.logging import setup_logging
from beams.service.helpers.worker import Worker
from beams.service.remote_calls.command_pb2 import CommandMessage, CommandType
from beams.service.rpc_handler import RPCHandler
from beams.service.tree_ticker import TreeState, TreeTicker

logger = logging.getLogger(__name__)


class BeamsService(Worker):
    def __init__(self):
        # TODO: make a singleton. Make process safe by leaving artifact file
        super().__init__("BeamsService", grace_window_before_terminate_seconds=0.5)

        # remote manager: https://docs.python.org/3/library/multiprocessing.html#using-a-remote-manager
        class SyncMan(BaseManager):
          pass

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
                logger.debug(f"Cleaning up tree of name {tree_name}")
                tree.stop_work()
                tree.shutdown()

    def work_func(self):
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
                        self.load_new_tree(request)
                    elif (request.command_t == CommandType.START_TREE):
                        self.start_tree(request)
                    elif (request.command_t == CommandType.PAUSE_TREE):
                        self.pause_tree(request)
                    elif (request.command_t == CommandType.TICK_TREE):
                        self.tick_tree(request)

            except Exception:
                logger.exception('Exception caught')
        self.grpc_service.stop_work()

    def load_new_tree(self, request: CommandMessage) -> None:
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
            logger.debug(f"Loaded tree of name {request.tree_name}" +
                         f" from filepath: {request.load_new_tree.tree_file_path}" +
                         " explciit START_TREE command will need to be issued for it to begin")

    def start_tree(self, request: CommandMessage) -> None:
        with self.sync_man as man:
            # get tree, again for now this is tree specified in json file,
            # disambugiate this later
            tree_name = request.tree_name
            # get tree
            tree_dict = man.get_tree_dict()
            if (tree_name not in tree_dict.keys()):
                logging.error(f"{tree_name} is not in tree_dictionary: {tree_dict}")
                return
            tree_to_start = tree_dict.get(tree_name)
            tree_to_start.start_tree()

    def pause_tree(self, request: CommandMessage) -> None:
        with self.sync_man as man:
            # get tree, again for now this is tree specified in json file,
            # disambugiate this later
            tree_name = request.tree_name
            # get tree
            tree_dict = man.get_tree_dict()
            if (tree_name not in tree_dict.keys()):
                logging.error(f"{tree_name} is not in tree_dictionary: {tree_dict}")
                return
            tree_to_start = tree_dict.get(tree_name)
            tree_to_start.pause_tree()

    def tick_tree(self, request: CommandMessage) -> None:
        with self.sync_man as man:
            # get tree, again for now this is tree specified in json file,
            # disambugiate this later
            tree_name = request.tree_name
            # get tree
            tree_dict = man.get_tree_dict()
            if (tree_name not in tree_dict.keys()):
                logging.error(f"{tree_name} is not in tree_dictionary: {tree_dict}")
                return
            tree_to_start = tree_dict.get(tree_name)
            tree_to_start.command_tick()


def main(*args, **kwargs):
    x = BeamsService()
    x.start_work()

    while (input("press q to kill") != 'q'):
        time.sleep(1)
    x.join_all_trees()
    x.stop_work()


if __name__ == "__main__":
    setup_logging(logging.DEBUG)
    main()
