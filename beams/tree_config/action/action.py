import logging
from dataclasses import dataclass, field
import time

import numpy as np
import cv2 as cv

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
        cam.acquire.put(1)
        # should check frequency being reported by camera

        for i in range(20):  # TODO make average configurable
          self.image_frame += cam.image1.image
          time.sleep(0.1)  # TODO: can do it the same way as camviewer which accumulates at cam freq
        self.image_frame /= 20

        cam.led.put(0)

        normalized = np.zeros((1024, 1024))
        normalized = cv.normalize(self.image_frame, normalized, 0, 190, cv.NORM_MINIMAX).astype('uint8')

        blur = cv.medianBlur(normalized, 5)

        # adaptive threshold
        thresh = cv.adaptiveThreshold(blur, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, 71, -9)

        # morph_open: more noise reduction
        open_kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3))
        opened = cv.morphologyEx(thresh, cv.MORPH_OPEN, open_kernel)
        
        # morph_close: expand fiducials into full squares
        dilate_kernel = cv.getStructuringElement(cv.MORPH_RECT, (12, 12))
        dilate = cv.morphologyEx(opened, cv.MORPH_DILATE, dilate_kernel)

        edges = cv.Canny(dilate, 50, 150)