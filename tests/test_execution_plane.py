import pytest

from aurelix_runtime.execution_plane import ExecutionDenied, ExecutionPlane, ExecutionScope


def test_execution_requires_explicit_engine_permission() -> None:
    plane = ExecutionPlane()
    plane.register("research", lambda payload: {"ok": True, **payload})
    scope = ExecutionScope("agent-research", frozenset({"research"}), max_runtime_seconds=1)
    receipt = plane.execute(scope, "research", {"query": "test"})
    assert receipt.status == "completed"
    assert receipt.output["ok"] is True


def test_execution_fails_closed_for_unscoped_engine() -> None:
    plane = ExecutionPlane()
    plane.register("business", lambda payload: {"executed": True})
    scope = ExecutionScope("agent-research", frozenset({"research"}))
    with pytest.raises(ExecutionDenied):
        plane.execute(scope, "business", {})


def test_unknown_engine_is_denied() -> None:
    plane = ExecutionPlane()
    scope = ExecutionScope("agent", frozenset({"research"}))
    with pytest.raises(ExecutionDenied):
        plane.execute(scope, "research", {})
