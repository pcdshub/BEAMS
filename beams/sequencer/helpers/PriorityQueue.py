"""
Thread safe priority queue
Warning this is not effecient to search, it is a dumb priority queue. If performance becomes an issue... this is python.
But also make it a binary tree, you could utilize the heapq library but it kind of sucks
"""

from queue import PriorityQueue as pqueue
from multiprocessing import Lock
import os


class PriorityQueue:
  def __init__(self, priority_dict):
    self.__queue__ = pqueue(maxsize=100)
    self.__priority_dict__ = priority_dict
    self.__lock__ = Lock()
    self.entry_count = 0

  def get_priority_int(self, prio_enum):
    try:
      return self.__priority_dict__[prio_enum]
    except KeyError:
      raise KeyError(f"Priority Enum provided {prio_enum} not in priority_dict")

  def put(self, ent, prio_enum):
    print(f"acquiring the put lock on {os.getpid()}")
    with self.__lock__:
      print("putting it in")
      self.__queue__.put((self.get_priority_int(prio_enum), 
                          self.entry_count,
                          ent))
      print(self.__queue__)
      self.entry_count += 1
    print("lock released")

  def pop(self):
    print(f"acquiring the lock for pop on {os.getpid()}")
    with self.__lock__:
      print(self.__queue__)
      val = self.__queue__.get()
      print(val)
      return val[-1]
    print("releasing lock for pop")
