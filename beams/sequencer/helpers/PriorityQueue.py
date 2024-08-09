"""
Thread safe priority queue
Warning this is not effecient to search, it is a dumb priority queue. If performance becomes an issue... this is python.
But also make it a binary tree, you could utilize the heapq library but it kind of sucks
"""

import heapq
import logging
import os
from multiprocessing import Lock, Pipe, Value


class PriorityQueue:
    def __init__(self, priority_dict):
        self.__queue__ = []
        self.__priority_dict__ = priority_dict
        self.__lock__ = Lock()
        self.entry_count = Value("d", 0)
        self.recv_sock, self.send_sock = Pipe(
            duplex=False
        )  # object for transfering pqueue between processes
        self.send_sock.send(self.__queue__)

    def get_priority_int(self, prio_enum):
        try:
            return self.__priority_dict__[prio_enum]
        except KeyError:
            raise KeyError(f"Priority Enum provided {prio_enum} not in priority_dict")

    def put(self, ent, prio_enum):
        logging.debug(f"acquiring the put lock on {os.getpid()}")
        with self.__lock__:
            logging.debug("getting queue")
            q = self.recv_sock.recv()
            logging.debug(f"got queue {q}, putting it in")
            heapq.heappush(
                q, (self.get_priority_int(prio_enum), self.entry_count.value, ent)
            )
            logging.debug(f"q is now {q}")
            self.__queue__ = q  # kinda just for posterity
            self.entry_count.value += 1  # safe due to lock object
            self.send_sock.send(q)
        logging.debug("lock released")

    def pop(self):
        logging.debug(f"acquiring the lock for pop on {os.getpid()}")
        with self.__lock__:
            logging.debug("getting queue")
            q = self.recv_sock.recv()
            logging.debug(f"got queue {q}")
            val = heapq.heappop(q)
            logging.debug(f"got val {val}")
            self.send_sock.send(q)
            self.__queue__ = q
            logging.debug(f"new queue {q}")
        logging.debug("releasing lock for pop")
        return val[-1]
