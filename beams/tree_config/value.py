import logging
from typing import Any
from dataclasses import dataclass

import py_trees
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


class BlackBoardValue(BaseValue):
    bb_name: str = ""
    key_name: str = ""

    def get_value(self) -> Any:
        logger.debug(f" <<-- (BlackBoardValue): checking blackboard: {self.bb_name} \
                      for key {self.key_name}")
        bb_client = py_trees.blackboard.Client(name=self.bb_name)
        try:
            value = bb_client.get(self.key_name)
        except AttributeError:  # Note: seems like it should be KeyError, but in practice getting this one
            logger.error(f"<<-- In blackboard: {self.bb_name} \
                          key {self.key_name} does not exist \
                          returning None")
            return None
        return value


@dataclass
class OphydTarget(BaseValue):
    device_name: str
    component_path: list[str]
