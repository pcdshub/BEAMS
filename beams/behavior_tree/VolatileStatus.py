from enum import Enum

from py_trees.common import Status

from beams.sequencer.helpers.SharedEnum import SharedEnum

"""
py_trees stores its enums as strings which is painful

"""


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
    Status.INVALID: IntStatus.INVALID,
    Status.FAILURE: IntStatus.FAILURE,
    Status.RUNNING: IntStatus.RUNNING,
    Status.SUCCESS: IntStatus.SUCCESS,
}

IntStatusToStatus = {
    IntStatus.INVALID: Status.INVALID,
    IntStatus.FAILURE: Status.FAILURE,
    IntStatus.RUNNING: Status.RUNNING,
    IntStatus.SUCCESS: Status.SUCCESS,
}


class VolatileStatus(SharedEnum):
    """
    Process safe helper for enum types
    Need to translate from py_trees string enum to normal enum
    """
    def __init__(self, init_status=Status.INVALID):
        super().__init__(StatusToIntStatus[init_status])

    def get_value(self):
        return IntStatusToStatus[super().get_value()]

    def set_value(self, status):
        super().set_value(StatusToIntStatus[status])


if __name__ == "__main__":
    VolatileStatus()
