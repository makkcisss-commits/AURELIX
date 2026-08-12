import pytest

from aurelix_core.audit import AuditLog
from aurelix_core.circuit_breaker import CircuitBreaker
from aurelix_core.execution import ExecutionRequest, ExecutionRuntime
from aurelix_core.execution_authorizer import AuthorizedExecution, ExecutionAuthorizationError
from aurelix_core.governor import Governor
from aurelix_core.models import ActionClass, Actor, AutonomyLevel, DecisionRequest
from aurelix_core.resource_scope import ResourceKind, ResourcePermission, ResourceRequest


def make_execution_request(actor_id: str = "research-agent") -> ExecutionRequest:
    permission = ResourcePermission(
        actor_id=actor_id,
        resource=ResourceKind.RESEARCH,
        operations=frozenset({"read"}),
        scope="project-alpha",
    )
    resource = ResourceRequest(actor_id, ResourceKind.RESEARCH, "read", "project-alpha")
    return ExecutionRequest(actor_id, resource, permission)


def make_decision_request(autonomy: AutonomyLevel = AutonomyLevel.A1) -> DecisionRequest:
    return DecisionRequest(
        actor=Actor(id="research-agent", role="agent", autonomy=autonomy),
        action=ActionClass.RESEARCH,
        reason="collect research",
    )


def test_governor_and_runtime_form_single_gate() -> None:
    audit = AuditLog()
    runtime = ExecutionRuntime(CircuitBreaker())
    service = AuthorizedExecution(Governor(audit=audit), runtime, audit)

    result = service.run(make_decision_request(), make_execution_request(), lambda: "ok")

    assert result.success
    assert result.output == "ok"
    assert any(event.event_type == "execution.completed" for event in audit.all())


def test_protected_action_stops_before_runtime() -> None:
    audit = AuditLog()
    service = AuthorizedExecution(Governor(audit=audit), ExecutionRuntime(), audit)
    request = DecisionRequest(
        actor=Actor("research-agent", "agent", AutonomyLevel.A1),
        action=ActionClass.FINANCIAL,
        reason="request payment",
    )

    with pytest.raises(ExecutionAuthorizationError):
        service.run(request, make_execution_request(), lambda: "must-not-run")

    assert any(event.event_type == "execution.blocked" for event in audit.all())
