import time
import pytest

from aurelix_runtime.execution_limits import DrainController, ExecutionLimits, ExecutionTimeout, execution_deadline


def test_drain_stops_new_work():
    drain = DrainController()
    assert drain.allow_new_work() is True
    drain.begin()
    assert drain.draining is True
    assert drain.allow_new_work() is False


def test_execution_deadline_reports_overrun():
    with pytest.raises(ExecutionTimeout):
        with execution_deadline(ExecutionLimits(timeout_seconds=0.001)):
            time.sleep(0.01)
