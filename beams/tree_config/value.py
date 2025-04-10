import logging
from ctypes import c_bool, c_int
from dataclasses import dataclass
from multiprocessing import Value
from typing import Any

from epics import caget

from beams.serialization import as_tagged_union

logger = logging.getLogger(__name__)


@as_tagged_union
@dataclass
class BaseValue:
    def get_value(self) -> Any:
        raise NotImplementedError


@dataclass
class FixedValue(BaseValue):
    value: Any

    def get_value(self) -> Any:
        return self.value


@dataclass
class EPICSValue(BaseValue):
    pv_name: str
    as_string: bool = False

    def get_value(self) -> Any:
        value = caget(self.pv_name, as_string=self.as_string)
        logger.debug(f" <<-- (EPICSValue): caget({self.pv_name}) -> {value}")
        return value


@dataclass
class ProcessIntValue(BaseValue):
    value: int = 0

    def __post_init__(self):
        self._value = Value(c_int, self.value, lock=True)

    def set_value(self, value: int):
        self._value.value = value

    def get_value(self) -> int:
        return self._value.value


@dataclass
class ProcessBoolValue(BaseValue):
    value: bool = False

    def __post_init__(self):
        self._value = Value(c_bool, self.value, lock=True)

    def set_value(self, value: bool):
        self._value.value = value

    def get_value(self) -> bool:
        return self._value.value


@dataclass
class OphydTarget(BaseValue):
    device_name: str
    component_path: list[str]
