import time
from multiprocessing import Process

from beams.sequencer.SequencerState import SequencerState, SequencerStatesVariables
from beams.sequencer.remote_calls.sequencer_pb2 import SequenceType, RunStateType, TickStatus, MessageType


class TestTask:
  def test_init(self, capsys):
    x = SequencerState()
    assert x.get_value(SequencerStatesVariables.sequence) == SequenceType.NONE
    assert x.get_value(SequencerStatesVariables.node_name) == b"None"
    assert x.get_value(SequencerStatesVariables.status) == TickStatus.UNKNOWN
    assert x.get_value(SequencerStatesVariables.run_state) == RunStateType.STATE_UNKNOWN

  def test_get_command_reply(self):
    x = SequencerState()
    y = x.get_command_reply()
    assert y[SequencerStatesVariables.sequence] == SequenceType.NONE
    assert y[SequencerStatesVariables.node_name] == b"None"
    assert y[SequencerStatesVariables.status] == TickStatus.UNKNOWN
    assert y[SequencerStatesVariables.run_state] == RunStateType.STATE_UNKNOWN
    assert y["mess_t"] == MessageType.MESSAGE_TYPE_COMMAND_REPLY

  def test_multi_access(self):
    x = SequencerState()

    def proc1work(x):
      print("proc1 a go")
      x.set_value(SequencerStatesVariables.run_state, RunStateType.TICKING)

    def proc2work(x):
      print("proc2 a go")
      while (x.get_value(SequencerStatesVariables.run_state) != RunStateType.TICKING):
        print("waiting for get value to return true")
        time.sleep(.1)

      assert x.get_value(SequencerStatesVariables.run_state) == RunStateType.TICKING

    proc1 = Process(target=proc1work, args=(x,))
    proc2 = Process(target=proc2work, args=(x,))
    proc2.start()
    time.sleep(.4)
    proc1.start()
