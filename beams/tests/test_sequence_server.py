from beams.sequencer.SequencerState import SequencerState
from beams.sequencer.SequenceServer import SequenceServer


class TestTask():
  def task1(self):
    p = SequenceServer(SequencerState())
    p.start_work()
