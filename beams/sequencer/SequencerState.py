from multiprocessing import Lock, Array, Value
from beams.sequencer.remote_calls.sequencer_pb2 import SequenceType, RunStateType, MessageType, TickStatus
from enum import Enum
import logging

SequencerStatesVariables = Enum('SequencerStatesVariables', 
                                ["sequence", 
                                 "node_name", 
                                 "status",
                                 "run_state"])


class SequencerState():
  """
  Object that provides threadsafe access to state variables of the sequencer
  """
  def __init__(self):
    self.__lock__ = Lock()
    self.state_dictionary = {i : 0 for i in SequencerStatesVariables}
    self.state_dictionary[SequencerStatesVariables.sequence] = Value('i', SequenceType.NONE, lock=self.__lock__)
    self.state_dictionary[SequencerStatesVariables.node_name] = Array('c', b'None', lock=self.__lock__)  # TODO: might want to wrap so we aren't dealing with byte strings 
    self.state_dictionary[SequencerStatesVariables.status] = Value('i', TickStatus.UNKNOWN, lock=self.__lock__)
    self.state_dictionary[SequencerStatesVariables.run_state] = Value('i', RunStateType.STATE_UNKNOWN, lock=self.__lock__)

  def get_command_reply(self) -> dict:
    """
    Return such that the dict can be unwaped and passed as kwargs to CommandReply message constructor via double splat op
    """
    with self.__lock__:
      command_reply = {k : v.value for k , v in self.state_dictionary.items()}
      command_reply.update({"mess_t" : MessageType.MESSAGE_TYPE_COMMAND_REPLY})
      return command_reply

  def set_all_values(self, current_sequence: SequenceType, current_node: str, current_tick_status: TickStatus, current_run_state: RunStateType) -> None:
    logging.debug("Acquiring lock for 'set_all_values'")
    with self.__lock__:
      self.state_dictionary[SequencerStatesVariables.current_sequence].value = current_sequence
      self.state_dictionary[SequencerStatesVariables.current_node_name].value = current_node
      self.state_dictionary[SequencerStatesVariables.current_status].value = current_tick_status
      self.state_dictionary[SequencerStatesVariables.current_run_state].value = current_run_state

  def set_value(self, state: SequencerStatesVariables, value):
    self.state_dictionary[state].value = value  # Todo(josh): wrap in try catch with log.

  def get_value(self, state: SequencerStatesVariables):
    return self.state_dictionary[state].value  # Todo(josh): wrap in try catch with log.
