import time
from multiprocessing import Process

from beams.sequencer.remote_calls.sequencer_pb2 import (MessageType,
                                                        RunStateType,
                                                        SequenceType,
                                                        TickStatus)
from beams.sequencer.SequencerState import (SequencerState,
                                            SequencerStateVariable)


class TestTask:
    def test_init(self, capsys):
        x = SequencerState()
        assert x.get_value(SequencerStateVariable.SEQUENCE) == SequenceType.NONE
        assert x.get_value(SequencerStateVariable.NODE_NAME) == b"None"
        assert x.get_value(SequencerStateVariable.STATUS) == TickStatus.UNKNOWN
        assert (
            x.get_value(SequencerStateVariable.RUN_STATE) == RunStateType.STATE_UNKNOWN
        )

    def test_get_command_reply(self):
        x = SequencerState()
        y = x.get_command_reply()
        print(y)
        assert y[SequencerStateVariable.SEQUENCE.value] == SequenceType.NONE
        assert y[SequencerStateVariable.NODE_NAME.value] == b"None"
        assert y[SequencerStateVariable.STATUS.value] == TickStatus.UNKNOWN
        assert y[SequencerStateVariable.RUN_STATE.value] == RunStateType.STATE_UNKNOWN
        assert y["mess_t"] == MessageType.MESSAGE_TYPE_COMMAND_REPLY

    def test_multi_access(self):
        x = SequencerState()

        def proc1work(x):
            print("proc1 a go")
            x.set_value(SequencerStateVariable.RUN_STATE, RunStateType.TICKING)

        def proc2work(x):
            print("proc2 a go")
            while x.get_value(SequencerStateVariable.RUN_STATE) != RunStateType.TICKING:
                print("waiting for get value to return true")
                time.sleep(0.1)

            assert x.get_value(SequencerStateVariable.RUN_STATE) == RunStateType.TICKING

        proc1 = Process(target=proc1work, args=(x,))
        proc2 = Process(target=proc2work, args=(x,))
        proc2.start()
        time.sleep(0.4)
        proc1.start()
