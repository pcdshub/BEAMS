import logging
from dataclasses import dataclass, field
import time

import numpy as np

import py_trees
from epics import caget, caput

from beams.typing_helper import Evaluatable
from beams.behavior_tree.action_node import ActionNode, wrapped_action_work
from beams.tree_config.base import BaseItem

from beams.devices import YagCamera

logger = logging.getLogger(__name__)


@dataclass
class FindReticuleTransform(BaseItem):
  camera_name: str = ""
  camera_prefix: str = ""

  def __post_init__(self):
    self.image_frame = np.zeros((1024, 1024))

  def get_tree(self) -> ActionNode:

    cam = YagCamera(name=self.camera_name, prefix=self.camera_prefix)

    @wrapped_action_work
    def work_func(comp_condition: Evaluatable) -> py_trees.common.Status:
        # configure camera to acquire an image
        cam.led.put(1)
        cam.exposure.put(0.001)
        target = 'RETICLE'
        cam.acquire.put(1)
        # should check frequency being reported by camera
        time.sleep(2)

        self.image_frame = cam.image1.image
        cam.led.put(0)
