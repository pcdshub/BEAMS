from multiprocessing import Value
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
