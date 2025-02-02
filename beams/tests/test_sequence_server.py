from beams.service.rpc_handler import RPCHandler
from beams.service.state import SequencerState


class TestTask:
    def task1(self):
        p = RPCHandler(SequencerState())
        p.start_work()
