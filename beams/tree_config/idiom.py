from __future__ import annotations

import logging
from copy import copy
from dataclasses import dataclass, field
from typing import Union

from beams.behavior_tree.check_and_do import CheckAndDo
from beams.tree_config.action import IncPVActionItem, SetPVActionItem
from beams.tree_config.base import BaseItem
from beams.tree_config.condition import BaseConditionItem, DummyConditionItem

logger = logging.getLogger(__name__)


@dataclass
class CheckAndDoItem(BaseItem):
    check: BaseConditionItem = field(default_factory=DummyConditionItem)
    do: Union[SetPVActionItem, IncPVActionItem] = field(default_factory=SetPVActionItem)

    def __post_init__(self):
        # Clearly indicate the intent for serialization
        # If termination check is the default default, create the dummy item instead
        if self.do.termination_check == DummyConditionItem():
            self.do.termination_check = UseCheckConditionItem(
                name=f"{self.do.name}_termination_check",
                description=f"Use parent's check node: {self.check.name}"
            )

    def get_tree(self) -> CheckAndDo:
        if isinstance(self.do.termination_check, UseCheckConditionItem):
            active_do = copy(self.do)
            active_do.termination_check = self.check
        else:
            active_do = self.do

        check_node = self.check.get_tree()
        do_node = active_do.get_tree()

        node = CheckAndDo(name=self.name, check=check_node, do=do_node)

        return node


@dataclass
class UseCheckConditionItem(BaseConditionItem):
    """
    Dummy item: indicates that check and do should use "check" as do's termination check.

    If used in any other context the tree will not be constructable.
    """
    ...
