import logging

import py_trees.logging
import pytest

from beams.logging import setup_logging


@pytest.fixture(autouse=True)
def logging_setup(caplog):
    # Set pytest debugging level, and capture that output
    # Without this logging calls made after the test may fire after the listener
    # thread is closed.
    caplog.set_level(logging.DEBUG)
    # set debug level in case people are curious
    setup_logging(logging.DEBUG)
    # Set py_trees logging level (not our library)
    py_trees.logging.level = py_trees.logging.Level.DEBUG
