from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .audit import AuditEvent, AuditLog
from .budget import Budget
from .circuit_breaker import CircuitBreaker
from .execution import ExecutionRequest, ExecutionResult, ExecutionRuntime
from .governor import Governor
from .models import DecisionRequest, DecisionStatus


class ControlPlaneDenied(Exception):
    """Raised when the unified control plane blocks execution."""


@dataclass
class ControlPlane:
    """Deterministic orchestration boundary for protected execution.

    This layer composes existing guards. It does not grant new authority and
    it never interprets model output as permission.
    """

    governor: Governor
    runtime: ExecutionRuntime
    audit: AuditLog

    @classmethod
    def create(cls, governor: Governor | None = None, audit: AuditLog | None = None) -> "ControlPlane":
        sink = audit or AuditLog()
        runtime = ExecutionRuntime(CircuitBreaker())
        return cls(
            governor=governor or Governor(audit=sink),
            runtime=runtime,
            audit=sink,
        )

    def authorize(
        self,
        decision_request: DecisionRequest,
        execution_request: ExecutionRequest,
        operation: Callable[[], object],
        budget: Budget | None = None,
        estimated_cost: str | None = None,
    ) -> ExecutionResult:
        decision = self.governor.evaluate(decision_request)
        if not decision.allowed or decision.requires_owner:
            self._blocked(decision_request.id, decision_request.actor.id, decision.status, decision.reason)
            raise ControlPlaneDenied(decision.reason)

        if budget is not None and estimated_cost is not None:
            try:
                budget.authorize(estimated_cost)
            except Exception as exc:
                self._blocked(decision_request.id, decision_request.actor.id, DecisionStatus.REJECTED, str(exc))
                raise ControlPlaneDenied(str(exc)) from exc

        result = self.runtime.execute(execution_request, operation)

        if budget is not None and estimated_cost is not None:
            budget.consume(estimated_cost)

        self.audit.append(
            AuditEvent(
                event_type="control_plane.completed",
                actor_id=decision_request.actor.id,
                subject_id=decision_request.id,
                outcome="success",
                metadata={"action": decision_request.action.value},
            )
        )
        return result

    def _blocked(self, subject_id: str, actor_id: str, status: DecisionStatus, reason: str) -> None:
        self.audit.append(
            AuditEvent(
                event_type="control_plane.blocked",
                actor_id=actor_id,
                subject_id=subject_id,
                outcome=status.value,
                metadata={"reason": reason},
            )
        )
