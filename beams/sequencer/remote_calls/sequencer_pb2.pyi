from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SequenceType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    NONE: _ClassVar[SequenceType]
    SAFE: _ClassVar[SequenceType]
    SELF_TEST: _ClassVar[SequenceType]
    CHANGE_GMD_GAS: _ClassVar[SequenceType]

class RunStateType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    STATE_UNKNOWN: _ClassVar[RunStateType]
    PAUSE: _ClassVar[RunStateType]
    STOP_AND_SAFE: _ClassVar[RunStateType]
    RESUME: _ClassVar[RunStateType]
    DEBUG: _ClassVar[RunStateType]
    TICKING: _ClassVar[RunStateType]
    WAIT_FOR_TICK: _ClassVar[RunStateType]

class MessageType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    MESSAGE_TYPE_UNKOWN: _ClassVar[MessageType]
    MESSAGE_TYPE_ALTER_RUN_STATE: _ClassVar[MessageType]
    MESSAGE_TYPE_ENQUEUE_SEQUENCE_PRIORITY: _ClassVar[MessageType]
    MESSAGE_TYPE_ENQUEUE_SEQUENCE: _ClassVar[MessageType]
    MESSAGE_TYPE_COMMAND_REPLY: _ClassVar[MessageType]

class TickStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
    UNKNOWN: _ClassVar[TickStatus]
    RUNNING: _ClassVar[TickStatus]
    SUCCESS: _ClassVar[TickStatus]
    FAILURE: _ClassVar[TickStatus]
NONE: SequenceType
SAFE: SequenceType
SELF_TEST: SequenceType
CHANGE_GMD_GAS: SequenceType
STATE_UNKNOWN: RunStateType
PAUSE: RunStateType
STOP_AND_SAFE: RunStateType
RESUME: RunStateType
DEBUG: RunStateType
TICKING: RunStateType
WAIT_FOR_TICK: RunStateType
MESSAGE_TYPE_UNKOWN: MessageType
MESSAGE_TYPE_ALTER_RUN_STATE: MessageType
MESSAGE_TYPE_ENQUEUE_SEQUENCE_PRIORITY: MessageType
MESSAGE_TYPE_ENQUEUE_SEQUENCE: MessageType
MESSAGE_TYPE_COMMAND_REPLY: MessageType
UNKNOWN: TickStatus
RUNNING: TickStatus
SUCCESS: TickStatus
FAILURE: TickStatus

class GenericMessage(_message.Message):
    __slots__ = ["mess_t"]
    MESS_T_FIELD_NUMBER: _ClassVar[int]
    mess_t: MessageType
    def __init__(self, mess_t: _Optional[_Union[MessageType, str]] = ...) -> None: ...

class SequenceCommand(_message.Message):
    __slots__ = ["mess_t", "seq_t"]
    MESS_T_FIELD_NUMBER: _ClassVar[int]
    SEQ_T_FIELD_NUMBER: _ClassVar[int]
    mess_t: MessageType
    seq_t: SequenceType
    def __init__(self, mess_t: _Optional[_Union[MessageType, str]] = ..., seq_t: _Optional[_Union[SequenceType, str]] = ...) -> None: ...

class AlterState(_message.Message):
    __slots__ = ["mess_t", "stateToUpdateTo"]
    MESS_T_FIELD_NUMBER: _ClassVar[int]
    STATETOUPDATETO_FIELD_NUMBER: _ClassVar[int]
    mess_t: MessageType
    stateToUpdateTo: RunStateType
    def __init__(self, mess_t: _Optional[_Union[MessageType, str]] = ..., stateToUpdateTo: _Optional[_Union[RunStateType, str]] = ...) -> None: ...

class GenericCommand(_message.Message):
    __slots__ = ["mess_t", "seq_m", "alt_m"]
    MESS_T_FIELD_NUMBER: _ClassVar[int]
    SEQ_M_FIELD_NUMBER: _ClassVar[int]
    ALT_M_FIELD_NUMBER: _ClassVar[int]
    mess_t: MessageType
    seq_m: SequenceCommand
    alt_m: AlterState
    def __init__(self, mess_t: _Optional[_Union[MessageType, str]] = ..., seq_m: _Optional[_Union[SequenceCommand, _Mapping]] = ..., alt_m: _Optional[_Union[AlterState, _Mapping]] = ...) -> None: ...

class CommandReply(_message.Message):
    __slots__ = ["mess_t", "sequence", "node_name", "status", "run_state"]
    MESS_T_FIELD_NUMBER: _ClassVar[int]
    SEQUENCE_FIELD_NUMBER: _ClassVar[int]
    NODE_NAME_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RUN_STATE_FIELD_NUMBER: _ClassVar[int]
    mess_t: MessageType
    sequence: SequenceType
    node_name: str
    status: TickStatus
    run_state: RunStateType
    def __init__(self, mess_t: _Optional[_Union[MessageType, str]] = ..., sequence: _Optional[_Union[SequenceType, str]] = ..., node_name: _Optional[str] = ..., status: _Optional[_Union[TickStatus, str]] = ..., run_state: _Optional[_Union[RunStateType, str]] = ...) -> None: ...

class Empty(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...
