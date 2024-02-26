from beams.sequencer.helpers.PriorityQueue import PriorityQueue
from enum import IntEnum


class Color(IntEnum):
  RED = 0
  YELLOW = 1
  GREEN = 2


class TestTask():
  def test_1(self):
    priority_dict = {
      Color.RED : 0,
      Color.YELLOW : 1,
      Color.GREEN : 2
    }
    p = PriorityQueue(priority_dict)

    p.put("egg", Color.YELLOW)
    p.put("josh", Color.GREEN)
    p.put("hyuh", Color.RED)
    p.put("will", Color.YELLOW)

    assert p.pop() == "hyuh"
    assert p.pop() == "egg"
    assert p.pop() == "will"
    assert p.pop() == "josh"
