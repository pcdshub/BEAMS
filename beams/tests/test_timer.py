import time

import pytest

from beams.sequencer.helpers.timer import Timer


def test_elapsed():
    t = Timer(name="test_elapsed",
              timer_period_seconds=0.1,
              is_periodic=False)
    t.start_timer()
    assert not t.is_elapsed()
    time.sleep(0.5)
    assert t.is_elapsed()


def test_timer_error():
    t = Timer(name="test_error_not_started",
              timer_period_seconds=0.1,
              is_periodic=False)
    with pytest.raises(RuntimeError):
        t.get_elapsed()
    with pytest.raises(RuntimeError):
        t.is_elapsed()


def test_periodic():
    t = Timer(name="test_error_not_started",
              timer_period_seconds=0.1,
              auto_start=True,
              is_periodic=True)
    time.sleep(0.2)
    assert t.is_elapsed()
    assert not t.is_elapsed()
    time.sleep(0.1)
    assert t.is_elapsed()
