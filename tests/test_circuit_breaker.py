import pytest

from aurelix_core.circuit_breaker import CircuitBreaker, CircuitOpen, CircuitState


def test_breaker_starts_closed() -> None:
    breaker = CircuitBreaker(failure_threshold=2)
    assert breaker.state is CircuitState.CLOSED
    assert breaker.allow()


def test_breaker_opens_at_failure_threshold() -> None:
    breaker = CircuitBreaker(failure_threshold=2)
    breaker.record_failure()
    assert breaker.allow()
    breaker.record_failure()
    assert breaker.state is CircuitState.OPEN
    assert not breaker.allow()


def test_open_breaker_blocks_execution() -> None:
    breaker = CircuitBreaker(failure_threshold=1)
    breaker.record_failure()
    with pytest.raises(CircuitOpen):
        breaker.require_allowed()


def test_success_resets_failures() -> None:
    breaker = CircuitBreaker(failure_threshold=3)
    breaker.record_failure()
    breaker.record_failure()
    breaker.record_success()
    assert breaker.state is CircuitState.CLOSED
    assert breaker.failures == 0
