"""
* An base class for child classes whos main function is to support a work thread.
* Holds volatile `self.do_work` which is intended to handle kill signal.
* Provides `start_work` and `stop_work` functions to spawn and stop work processes.
* Optional arg `stop_func` run on process termination before joining work process.
"""
import logging
import time
from ctypes import c_bool
from multiprocessing import Process, Value
from multiprocessing.sharedctypes import Synchronized
from typing import Any, Callable, List, Optional

logger = logging.getLogger(__name__)


class Worker():
    def __init__(
        self,
        proc_name: str,
        stop_func: Optional[Callable[[None], None]] = None,
        work_func: Optional[Callable[[Any], None]] = None,
        proc_type: type[Process] = Process,
        add_args: Optional[List[Any]] = None,
    ):
        self.do_work: Synchronized = Value(c_bool, False)
        self.proc_name = proc_name
        self.proc_type = proc_type
        self.add_args = add_args or []
        if (work_func is None):
          self.work_proc = proc_type(target=self.work_func, name=self.proc_name)
        else:
          self.work_func = work_func
          # Critical Note: This makes assumptions of the work_func signature
          # in that it takes a Value argument in position 0
          self.work_proc = proc_type(target=self.work_func,
                                     name=self.proc_name,
                                     args=(self.do_work, *self.add_args,))
        self.stop_func = stop_func

    def start_work(self):
        if self.do_work.value:
            logger.error(f"({self.proc_name}) -->>: Already working, cannot start")
            return
        self.do_work.value = True
        self.work_proc.start()
        logger.debug(f"({self.proc_name}) -->>: Starting work")

    def stop_work(self):
        logger.debug(f"({self.proc_name}) -->>: Calling stop work")
        if not self.do_work.value:
            logger.error(f"({self.proc_name}) -->>: Not working, not stopping work")
            return
        self.do_work.value = False
        logger.debug(f"({self.proc_name}) -->>: Sending terminate signal to process")
        time.sleep(0.5)
        # Send kill signal to work process. # TODO: the exact location of this
        # is important. Reflect with self.do_work.get_lock():
        self.work_proc.terminate()
        if (self.stop_func is not None):
            self.stop_func()

        logger.debug(f"({self.proc_name}) -->>: Ending work, calling join")
        self.work_proc.join()
        logger.debug(f"({self.proc_name}) -->>: Worker process joined")

    def work_func(self):
        """
        Example of what a work func can look like
        while(self.do_work.value):
          print(f"hi: {self.do_work.value}")
          time.sleep(1)
        logging.info(f"Work thread: {self.work_proc.pid} exit")
        """
        raise NotImplementedError("Implement a work function in the child class!")
