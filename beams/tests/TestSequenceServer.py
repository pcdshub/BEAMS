from beams.sequencer.SequenceServer import SequenceServer
from beams.sequencer.SequencerState import SequencerState


class TestTask():
  def task1(self):
    p = SequenceServer(SequencerState())
    p.start_work()
  
  