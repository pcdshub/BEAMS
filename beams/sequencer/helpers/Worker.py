"""
* An base class for child classes whos main function is to support a work thread.
* Holds volatile `self.do_work` which is intended to handle kill signal
* Provides `start_work` and `stop_work` functions to spawn and stop work processes
* Optional constructor arg `stop_func` to be executde on process termination before joining work process.
"""
import logging
from multiprocessing import Process, Value
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
        self.do_work = Value('i', False)
        self.proc_name = proc_name
        self.proc_type = proc_type
        self.add_args = add_args or []
        # TODO: we may want to decorate work func so it prints proc id...
        if (work_func is None):
          self.work_proc = proc_type(target=self.work_func, name=self.proc_name)
        else:
          self.work_func = work_func
          self.work_proc = proc_type(target=self.work_func, 
                                     name=self.proc_name,
                                     args=(self, *self.add_args,))
        self.stop_func = stop_func

    def start_work(self):
        if self.do_work.value:
            logger.error("Already working, not starting work")
            return
        self.do_work.value = True
        self.work_proc.start()
        logger.debug("Starting work")

    def stop_work(self):
        logger.debug("Calling stop work on")
        if not self.do_work.value:
            logger.error("Not working, not stopping work")
            return
        self.do_work.value = False
        logger.debug("Sending terminate signal to process")
        # Send kill signal to work process. # TODO: the exact location of this
        # is important. Reflect with self.do_work.get_lock():
        self.work_proc.terminate()
        if (self.stop_func is not None):
            self.stop_func()

        logger.debug("Ending work, calling join")
        self.work_proc.join()
        logger.debug("Worker process joined")

    def work_func(self):
        """
        Example of what a work func can look like
        while(self.do_work.value):
          print(f"hi: {self.do_work.value}")
          time.sleep(1)
        logging.info(f"Work thread: {self.work_proc.pid} exit")
        """
        raise NotImplementedError("Implement a work function in the child class!")
