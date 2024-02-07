from multiprocessing import Lock
from beams.sequencer.remote_calls.sequencer_pb2 import SequenceType, RunStateType, MessageType, TickStatus


class SharedCommandReply():
  def __init__(self):
    self.current_sequence = SequenceType.NONE
    self.current_node = "None"
    self.current_tick_status = TickStatus.UNKNOWN
    self.current_run_state = RunStateType.STATE_UNKNOWN
    self.__lock__ = Lock()
  
  def get_value(self):
    """
    Return such that the tuple can be unwaped and passed as an arg to CommandReply message constructor
    """
    with self.__lock__:
      return (MessageType.MESSAGE_TYPE_COMMAND_REPLY,
              self.current_sequence,
              self.current_node,
              self.current_tick_status,
              self.current_run_state)

  def set_value(self, current_sequence, current_node, current_tick_status, current_run_state):
    with self.__lock__:
      self.current_sequence = current_sequence
      self.current_node = current_node
      self.current_tick_status = current_tick_status
      self.current_run_state = current_run_state
