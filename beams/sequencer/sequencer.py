import logging
import os
import time
from multiprocessing import Event
from queue import Queue
from threading import Thread

import py_trees

from beams.sequencer.helpers.worker import Worker
from beams.sequencer.server import SequenceServer
from beams.sequencer.state import SequencerState
from beams.tree_generator.TreeGenerator import GenerateTreeFromRequest

logger = logging.getLogger(__name__)


class Sequencer(Worker):
    def __init__(self):
        super().__init__("Sequencer")
        # state maintenece object
        self.state = SequencerState()
        self.job_queue = Queue()
        self.job_ready = Event()

    def message_thread(self):
        """
        Parse messages into trees to be ticked.
        Insert into the relevant place in the job_queue, set job_ready event
        """
        logger.debug(f"{self.proc_name} running on pid: {os.getpid()}")
        while self.do_work.value:
            self.sequence_server.message_ready_sem.acquire()  # block untill we get something to work on
            request = self.sequence_server.message_queue.pop()
            logger.debug(f"request: {request}")
            job = GenerateTreeFromRequest(request)
            logger.debug(f"job: {job}")
            self.job_queue.put(job)
            self.job_ready.set()

    def work_func(self):
        """
        Spawn all needed workthreads:
        * GRPC Server
        * Message Handler
        Tick trees representing jobs to do in job_queue
        """
        logger.debug(f"{self.proc_name} running")
        # GRPC server object
        self.sequence_server = SequenceServer(self.state)
        self.sequence_server.start_work()  # TODO: move to work thread
        # Message Handler thread
        self.message_worker = Thread(name="message_handler", target=self.message_thread)
        self.message_worker.start()

        # Handle Work Queue
        while self.do_work.value:
            self.job_ready.wait()
            logger.debug("Sequencer ready for job")
            # invoke the function build out the root of the tree
            job = self.job_queue.get()()
            logger.debug(f"SUCC GET job root status: {job.root.status}")
            while (
                job.root.status != py_trees.common.Status.SUCCESS
                and job.root.status != py_trees.common.Status.FAILURE
            ):
                for n in job.root.tick():
                    logger.debug(f"ticking: {n}")
                    time.sleep(0.5)
                    logger.debug(f"status of tick: {n.status}")

            logger.debug(f"{job} done")


if __name__ == "__main__":
    s = Sequencer()
    s.start_work()
