from beams.service.server import SequenceServer
from beams.service.state import SequencerState


class TestTask:
    def task1(self):
        p = SequenceServer(SequencerState())
        p.start_work()
