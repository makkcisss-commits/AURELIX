from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .audit import AuditEvent, AuditLog
from .circuit_breaker import CircuitBreaker
from .execution import ExecutionRequest, ExecutionResult, ExecutionRuntime
from .governor import Governor
from .models import DecisionRequest, DecisionStatus


class ExecutionAuthorizationError(Exception):
    """Raised when the Governor does not authorize execution."""


@dataclass
class AuthorizedExecution:
    governor: Governor
    runtime: ExecutionRuntime
    audit: AuditLog

    def run(
        self,
        decision_request: DecisionRequest,
        execution_request: ExecutionRequest,
        operation: Callable[[], object],
    ) -> ExecutionResult:
        decision = self.governor.evaluate(decision_request)

        if decision.requires_owner or not decision.allowed:
            self.audit.append(
                AuditEvent(
                    event_type="execution.blocked",
                    actor_id=decision_request.actor.id,
                    subject_id=decision_request.id,
                    outcome=decision.status.value,
                    metadata={"reason": decision.reason},
                )
            )
            raise ExecutionAuthorizationError(decision.reason)

        result = self.runtime.execute(execution_request, operation)
        self.audit.append(
            AuditEvent(
                event_type="execution.completed",
                actor_id=decision_request.actor.id,
                subject_id=decision_request.id,
                outcome="success",
                metadata={"result_type": type(result.output).__name__},
            )
        )
        return result
