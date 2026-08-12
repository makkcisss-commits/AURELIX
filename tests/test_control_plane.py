from decimal import Decimal

import pytest

from aurelix_core.audit import AuditLog
from aurelix_core.budget import Budget
from aurelix_core.control_plane import ControlPlane, ControlPlaneDenied
from aurelix_core.execution import ExecutionRequest
from aurelix_core.models import ActionClass, Actor, AutonomyLevel, DecisionRequest
from aurelix_core.resource_scope import ResourceKind, ResourcePermission, ResourceRequest


def make_pair() -> tuple[DecisionRequest, ExecutionRequest]:
    actor = Actor("research-agent", "agent", AutonomyLevel.A1)
    decision = DecisionRequest(actor=actor, action=ActionClass.RESEARCH, reason="collect research")
    permission = ResourcePermission(
        actor_id=actor.id,
        resource=ResourceKind.RESEARCH,
        operations=frozenset({"read"}),
        scope="project-alpha",
    )
    resource = ResourceRequest(actor.id, ResourceKind.RESEARCH, "read", "project-alpha")
    return decision, ExecutionRequest(actor.id, resource, permission)


def test_control_plane_composes_governor_scope_runtime_and_budget() -> None:
    audit = AuditLog()
    plane = ControlPlane.create(audit=audit)
    decision, execution = make_pair()
    budget = Budget.create("EUR", "10")

    result = plane.authorize(decision, execution, lambda: "done", budget, "2.50")

    assert result.output == "done"
    assert budget.spent == Decimal("2.50")
    assert any(e.event_type == "control_plane.completed" for e in audit.all())


def test_control_plane_blocks_owner_required_action_before_operation() -> None:
    audit = AuditLog()
    plane = ControlPlane.create(audit=audit)
    actor = Actor("research-agent", "agent", AutonomyLevel.A1)
    decision = DecisionRequest(actor=actor, action=ActionClass.FINANCIAL, reason="spend money")
    _, execution = make_pair()
    called = False

    def operation() -> str:
        nonlocal called
        called = True
        return "must-not-run"

    with pytest.raises(ControlPlaneDenied):
        plane.authorize(decision, execution, operation)

    assert not called
    assert any(e.event_type == "control_plane.blocked" for e in audit.all())


def test_control_plane_blocks_budget_excess_before_operation() -> None:
    plane = ControlPlane.create()
    decision, execution = make_pair()
    budget = Budget.create("EUR", "1")
    called = False

    def operation() -> str:
        nonlocal called
        called = True
        return "must-not-run"

    with pytest.raises(ControlPlaneDenied):
        plane.authorize(decision, execution, operation, budget, "1.01")

    assert not called
