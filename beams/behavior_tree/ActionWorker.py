"""
A worker specialized to execute ActionNode work functions
"""
from typing import Callable, Any, Optional

from epics.multiproc import CAProcess

from beams.sequencer.helpers.Worker import Worker
from beams.behavior_tree.VolatileStatus import VolatileStatus


class ActionWorker(Worker):
    def __init__(self,
                 proc_name: str, 
                 volatile_status: VolatileStatus,
                 work_func: Callable[[Any], None],
                 comp_cond: Callable[[Any], bool],
                 stop_func: Optional[Callable[[None], None]] = None):
        super().__init__(proc_name=proc_name,
                         stop_func=stop_func,
                         work_func=work_func,
                         proc_type=CAProcess,
                         add_args=(comp_cond, volatile_status))
        self.comp_condition = comp_cond
        self.__volatile_status__ = volatile_status