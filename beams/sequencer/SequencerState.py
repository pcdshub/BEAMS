import logging
from enum import Enum
from multiprocessing import Array, Lock, Value

from beams.sequencer.remote_calls.sequencer_pb2 import (MessageType,
                                                        RunStateType,
                                                        SequenceType,
                                                        TickStatus)

logger = logging.getLogger(__name__)


class SequencerStateVariable(Enum):
    """
    StrEnum values must be kept in line with CommandReply's defined fields in the remote_calls/sequencer.proto file
    """

    SEQUENCE = "sequence"
    NODE_NAME = "node_name"
    STATUS = "status"
    RUN_STATE = "run_state"


class SequencerState:
    """
    Object that provides threadsafe access to state variables of the sequencer
    """

    def __init__(self):
        self.__lock__ = Lock()
        self.state_dictionary = {i: 0 for i in SequencerStateVariable}
        self.state_dictionary[SequencerStateVariable.SEQUENCE] = Value(
            "i", SequenceType.NONE
        )
        self.state_dictionary[SequencerStateVariable.NODE_NAME] = Array(
            "c", b"None"
        )  # TODO: wrap so we aren't dealing with byte strings
        self.state_dictionary[SequencerStateVariable.STATUS] = Value(
            "i", TickStatus.UNKNOWN
        )
        self.state_dictionary[SequencerStateVariable.RUN_STATE] = Value(
            "i", RunStateType.STATE_UNKNOWN
        )

    def get_command_reply(self) -> dict:
        """
        Return such that the dict can be unwaped and passed as kwargs to CommandReply message constructor via double splat op
        """
        with self.__lock__:
            command_reply = {k.value: v.value for k, v in self.state_dictionary.items()}
            command_reply.update({"mess_t": MessageType.MESSAGE_TYPE_COMMAND_REPLY})
            return command_reply

    def set_all_values(
        self,
        current_sequence: SequenceType,
        current_node: str,
        current_tick_status: TickStatus,
        current_run_state: RunStateType,
    ) -> None:
        logger.debug("Acquiring lock for 'set_all_values'")
        with self.__lock__:
            self.state_dictionary[
                SequencerStateVariable.SEQUENCE
            ].value = current_sequence
            self.state_dictionary[SequencerStateVariable.NODE_NAME].value = current_node
            self.state_dictionary[
                SequencerStateVariable.STATUS
            ].value = current_tick_status
            self.state_dictionary[
                SequencerStateVariable.RUN_STATE
            ].value = current_run_state

    def set_value(self, state: SequencerStateVariable, value):
        with self.state_dictionary[state].get_lock():
            self.state_dictionary[
                state
            ].value = value  # Todo(josh): wrap in try catch with log.

    def get_value(self, state: SequencerStateVariable):
        with self.state_dictionary[state].get_lock():
            val = self.state_dictionary[state].value
        return val  # Todo(josh): wrap in try catch with log.
