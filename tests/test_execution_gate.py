from aurelix_core.execution_gate import ExecutionContext, ExecutionGate, GateStatus


def ctx(**overrides):
    values = dict(
        approved=True,
        policy_allowed=True,
        budget_allowed=True,
        breaker_ready=True,
        audit_ready=True,
    )
    values.update(overrides)
    return ExecutionContext(**values)


def test_gate_is_ready_only_when_every_control_passes() -> None:
    result = ExecutionGate().evaluate(ctx())
    assert result.status is GateStatus.READY


def test_gate_fails_closed_when_owner_approval_is_missing() -> None:
    result = ExecutionGate().evaluate(ctx(approved=False))
    assert result.status is GateStatus.BLOCKED


def test_gate_fails_closed_for_any_other_blocking_control() -> None:
    for field in ("policy_allowed", "budget_allowed", "breaker_ready", "audit_ready"):
        result = ExecutionGate().evaluate(ctx(**{field: False}))
        assert result.status is GateStatus.BLOCKED
