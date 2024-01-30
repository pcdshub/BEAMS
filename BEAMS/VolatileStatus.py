from py_trees.common import Status
from multiprocessing import Value
from enum import Enum

'''
py_trees stores its enums as strings which is painful

'''


class IntStatus(Enum):
    """An enumerator representing the status of a behaviour."""

    SUCCESS = 3
    """Behaviour check has passed, or execution of its action has finished with a successful result."""
    FAILURE = 1
    """Behaviour check has failed, or execution of its action finished with a failed result."""
    RUNNING = 2
    """Behaviour is in the middle of executing some action, result still pending."""
    INVALID = 0
    """Behaviour is uninitialised and/or in an inactive state, i.e. not currently being ticked."""


StatusToIntStatus = {
  Status.INVALID : IntStatus.INVALID,
  Status.FAILURE : IntStatus.FAILURE,
  Status.RUNNING : IntStatus.RUNNING,
  Status.SUCCESS : IntStatus.SUCCESS
}

IntStatusToStatus = {
  IntStatus.INVALID : Status.INVALID,
  IntStatus.FAILURE : Status.FAILURE,
  IntStatus.RUNNING : Status.RUNNING,
  IntStatus.SUCCESS : Status.SUCCESS
}


'''
Thread (process) safe helpers 
'''


class SharedEnum():
  def __init__(self, enum):
    self.enum_val = enum
    self.enum_type = type(enum)
    print(self.enum_type)
    self.__safe_val__ = Value('i', enum.value)

  # return value as its enum type
  def get_value(self):
    with self.__safe_val__.get_lock():
      return self.enum_type(self.__safe_val__.value)

  def set_value(self, enum):
    with self.__safe_val__.get_lock():
      self.__safe_val__.value = enum.value

  def set_value_by_name(self, enum_name):
    with self.__safe_val__.get_lock():
      self.__safe_val__.value = self.enum_type[enum_name].value


'''
Process safe helper for enum types
Need to translate from py_trees string enum to normal enum
'''


class VolatileStatus(SharedEnum):
  def __init__(self, init_status=Status.INVALID):
    super().__init__(StatusToIntStatus[init_status])
  
  def get_value(self):
    return IntStatusToStatus[super().get_value()]

  def set_value(self, status):
    super().set_value(StatusToIntStatus[status])
