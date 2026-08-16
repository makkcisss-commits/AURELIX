import pytest

from aurelix_runtime.execution_plane import ExecutionDenied, ExecutionLimitExceeded, ExecutionPlane, ExecutionScope


def test_execution_requires_explicit_engine_permission() -> None:
    plane = ExecutionPlane()
    plane.register("research", lambda payload: {"ok": True, **payload})
    scope = ExecutionScope("agent-research", frozenset({"research"}), max_runtime_seconds=1)
    receipt = plane.execute(scope, "research", {"query": "test"})
    assert receipt.status == "completed"
    assert receipt.output["ok"] is True
    assert receipt.steps_used == 1


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


def test_multi_step_scope_requires_execution_identity() -> None:
    plane = ExecutionPlane()
    plane.register("research", lambda payload: {"ok": True})
    scope = ExecutionScope("agent", frozenset({"research"}), max_steps=2)
    with pytest.raises(ExecutionDenied, match="execution_id"):
        plane.execute(scope, "research", {})


def test_multi_step_scope_is_enforced_across_calls() -> None:
    plane = ExecutionPlane()
    plane.register("research", lambda payload: {"ok": True, **payload})
    scope = ExecutionScope("agent", frozenset({"research"}), max_steps=2, execution_id="exec-1")

    assert plane.execute(scope, "research", {"step": 1}).steps_used == 1
    assert plane.execute(scope, "research", {"step": 2}).steps_used == 2
    with pytest.raises(ExecutionLimitExceeded, match="step budget exhausted"):
        plane.execute(scope, "research", {"step": 3})


def test_execution_budget_can_be_reset_after_terminal_execution() -> None:
    plane = ExecutionPlane()
    plane.register("research", lambda payload: {"ok": True})
    scope = ExecutionScope("agent", frozenset({"research"}), max_steps=1, execution_id="exec-1")

    plane.execute(scope, "research", {})
    with pytest.raises(ExecutionLimitExceeded):
        plane.execute(scope, "research", {})

    plane.reset_execution("exec-1")
    assert plane.execute(scope, "research", {}).steps_used == 1
