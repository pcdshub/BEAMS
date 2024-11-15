from beams.sequencer.server import SequenceServer
from beams.sequencer.state import SequencerState


class TestTask:
    def task1(self):
        p = SequenceServer(SequencerState())
        p.start_work()
