import pytest

from aurelix_core.circuit_breaker import CircuitBreaker, CircuitOpen
from aurelix_core.execution import ExecutionDenied, ExecutionRequest, ExecutionRuntime
from aurelix_core.resource_scope import ResourceKind, ResourcePermission, ResourceRequest


def request() -> ExecutionRequest:
    permission = ResourcePermission(
        actor_id="research-agent",
        resource=ResourceKind.RESEARCH,
        operations=frozenset({"read"}),
        scope="project-alpha",
    )
    resource = ResourceRequest(
        actor_id="research-agent",
        resource=ResourceKind.RESEARCH,
        operation="read",
        target_scope="project-alpha",
    )
    return ExecutionRequest("research-agent", resource, permission)


def test_runtime_executes_authorized_operation() -> None:
    runtime = ExecutionRuntime()
    result = runtime.execute(request(), lambda: "research-result")
    assert result.success
    assert result.output == "research-result"


def test_runtime_denies_out_of_scope_operation() -> None:
    original = request()
    denied_resource = ResourceRequest(
        actor_id=original.resource.actor_id,
        resource=original.resource.resource,
        operation=original.resource.operation,
        target_scope="project-beta",
    )
    denied = ExecutionRequest(original.actor_id, denied_resource, original.permission)

    with pytest.raises(ExecutionDenied):
        ExecutionRuntime().execute(denied, lambda: "must-not-run")


def test_runtime_records_operation_failure() -> None:
    breaker = CircuitBreaker(failure_threshold=1)
    runtime = ExecutionRuntime(breaker)

    with pytest.raises(RuntimeError):
        runtime.execute(request(), lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    with pytest.raises(CircuitOpen):
        runtime.execute(request(), lambda: "blocked")
