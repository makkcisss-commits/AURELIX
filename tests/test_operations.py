import pytest

from aurelix_runtime.operations import OperationsController, RuntimeState, retry_bounded


def test_runtime_lifecycle_is_fail_closed() -> None:
    runtime = OperationsController()
    assert runtime.state is RuntimeState.BOOTING
    with pytest.raises(RuntimeError):
        runtime.start()
    runtime.ready()
    runtime.start()
    assert runtime.state is RuntimeState.RUNNING
    runtime.stop()
    assert runtime.state is RuntimeState.STOPPED


def test_retry_is_bounded() -> None:
    calls = 0

    def failing() -> object:
        nonlocal calls
        calls += 1
        raise ValueError("no")

    with pytest.raises(ValueError):
        retry_bounded(failing, max_retries=2)
    assert calls == 3


def test_invalid_limits_are_rejected() -> None:
    with pytest.raises(ValueError):
        OperationsController().limits.__class__(max_steps=0).validate()
