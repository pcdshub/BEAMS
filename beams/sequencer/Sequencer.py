import time

from beams.sequencer.helpers.Worker import Worker
from beams.sequencer.SequencerState import SequencerState, SequencerStateVariable
from beams.sequencer.SequenceServer import SequenceServer


class Sequencer(Worker):
  def __init__(self):
    super().__init__("Sequencer")
    self.state = SequencerState() 
    self.sequence_server = SequenceServer(self.state)
    self.sequence_server.start_work()

  def work_func(self):
    while (self.do_work.value):
      if (self.sequence_server.run_state_change_queue.qsize() != 0):
        mess = self.sequence_server.run_state_change_queue.get()
        self.state.set_value(SequencerStateVariable.RUN_STATE, mess.stateToUpdateTo)
      elif (self.sequence_server.sequence_request_queue.qsize() != 0):
        pass
      time.sleep(.1)


if __name__ == "__main__":
  s = Sequencer()
  s.start_work()
