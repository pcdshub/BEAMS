"""
typing helper:
Define commonly used "aggregator" types, lagerly custom function handles
Hint at rational behind function handles as entrypoint for debugging / learning
"""


from multiprocessing import Queue
from multiprocessing.sharedctypes import Synchronized  # type(Value)
from multiprocessing.synchronize import Event as EventClass
from typing import Callable

import py_trees

from beams.behavior_tree.volatile_status import VolatileStatus

# Evaluatable: function handle that returns a boolean , accpeting arbitrary arugments
Evaluatable = Callable[..., bool]

# Defines signature for an ActionNode work loop function handle.
# This is necessitated by how beams.behavior_tree.ActionWoker expects to spawn
# the work process via base class beams.service.helpers.Worker
# Parameter Types:
#   Synchronized: volatile Value indicating work remains to be performed
#                (tree is still ticking, program still running)
#   str: name of process
#   EventClass: work gate reflecting py_trees state of node with respect to tree
#   VolatileStatus: mechanism to signal from this process to other processes
#                   what the py_trees.common.Status of this node is
#   Evaluatable: this is a completion condition that allows exit of the while
#                loop within the work loop which will wait for a py_trees "initialise"
#                call to reset the Event (work gate) such that meaningful work
#                 can resume on this process
#   Queue: logging queue
#   Callable: mechanism to get logger
# Return Types:
#   None
ActionNodeWorkLoop = Callable[[Synchronized, str, EventClass, VolatileStatus, Evaluatable, Queue, Callable], None]

# Work function handle of function to be called during the RUNNING state of an ActionNode
# Parameter Types:
#   Evaluatable: determines what py_trees.common.Status to return
# Return Types:
#   py_trees.common.Status: reflects return type from this node with respect to tree logic
ActionNodeWorkFunction = Callable[[Evaluatable], py_trees.common.Status]
