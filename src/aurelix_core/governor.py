from __future__ import annotations

from .approvals import OwnerApproval, apply_owner_approval
from .audit import AuditEvent, AuditLog
from .models import Decision, DecisionRequest
from .policy import PolicyEngine


class Governor:
    """Central decision boundary for AURELIX.

    The Governor does not invent authority. It evaluates requests against policy,
    records the result, and exposes whether an owner gate is required.
    """

    def __init__(self, policy: PolicyEngine | None = None, audit: AuditLog | None = None) -> None:
        self.policy = policy or PolicyEngine()
        self.audit = audit or AuditLog()

    def evaluate(self, request: DecisionRequest) -> Decision:
        decision = self.policy.evaluate(request)
        self.audit.append(
            AuditEvent(
                event_type="decision.evaluated",
                actor_id=request.actor.id,
                subject_id=request.id,
                outcome=decision.status.value,
                metadata={
                    "action": request.action.value,
                    "allowed": decision.allowed,
                    "requires_owner": decision.requires_owner,
                },
            )
        )
        return decision

    def authorize_with_owner_approval(
        self,
        request: DecisionRequest,
        approval: OwnerApproval,
    ) -> Decision:
        """Apply a previously authenticated, scoped owner approval.

        Authentication is deliberately outside the core. This method only
        validates the domain scope of an approval and records the result.
        """
        decision = apply_owner_approval(request, approval)
        self.audit.append(
            AuditEvent(
                event_type="decision.owner_authorized",
                actor_id=approval.owner_id,
                subject_id=request.id,
                outcome=decision.status.value,
                metadata={
                    "approval_id": approval.approval_id,
                    "action": request.action.value,
                    "allowed": decision.allowed,
                },
            )
        )
        return decision
