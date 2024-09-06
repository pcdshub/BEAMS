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
