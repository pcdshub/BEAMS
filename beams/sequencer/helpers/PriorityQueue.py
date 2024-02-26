"""
Thread safe priority queue
Warning this is not effecient to search, it is a dumb priority queue. If performance becomes an issue... this is python.
But also make it a binary tree, you could utilize the heapq library but it kind of sucks
"""

import heapq
from multiprocessing import Lock


class PriorityQueue:
  def __init__(self, priority_dict):
    self.__queue__ = []
    self.__priority_dict__ = priority_dict
    self.__lock__ = Lock()
    self.entry_count = 0

  def get_priority_int(self, prio_enum):
    try:
      return self.__priority_dict__[prio_enum]
    except KeyError:
      raise KeyError(f"Priority Enum provided {prio_enum} not in priority_dict")

  def put(self, ent, prio_enum):
    with self.__lock__:
      heapq.heappush(self.__queue__, (self.get_priority_int(prio_enum), 
                                      self.entry_count, 
                                      ent))
      self.entry_count += 1

  def pop(self):
    return heapq.heappop(self.__queue__)[-1]
