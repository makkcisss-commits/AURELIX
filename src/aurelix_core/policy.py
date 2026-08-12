from __future__ import annotations

from .models import ActionClass, AutonomyLevel, Decision, DecisionRequest, DecisionStatus


class PolicyEngine:
    """Deterministic first-line authorization policy.

    This layer is intentionally conservative. Higher-risk actions can only become
    more permissive through an explicit policy change and tests.
    """

    _minimum_level = {
        ActionClass.READ: AutonomyLevel.A0,
        ActionClass.RESEARCH: AutonomyLevel.A1,
        ActionClass.BUILD: AutonomyLevel.A2,
        ActionClass.DEPLOY: AutonomyLevel.A4,
        ActionClass.FINANCIAL: AutonomyLevel.A4,
        ActionClass.SECURITY: AutonomyLevel.A4,
        ActionClass.GOVERNANCE: AutonomyLevel.A4,
    }

    _rank = {level: index for index, level in enumerate(AutonomyLevel)}

    def evaluate(self, request: DecisionRequest) -> Decision:
        minimum = self._minimum_level[request.action]
        actor_rank = self._rank[request.actor.autonomy]
        minimum_rank = self._rank[minimum]
        requires_owner = minimum_rank >= self._rank[AutonomyLevel.A4]

        if requires_owner:
            return Decision(
                request_id=request.id,
                status=DecisionStatus.PROPOSED,
                allowed=False,
                reason="Protected action requires explicit owner authorization.",
                requires_owner=True,
            )

        if actor_rank < minimum_rank:
            return Decision(
                request_id=request.id,
                status=DecisionStatus.REJECTED,
                allowed=False,
                reason=f"Actor autonomy {request.actor.autonomy.value} is below required {minimum.value}.",
                requires_owner=False,
            )

        return Decision(
            request_id=request.id,
            status=DecisionStatus.APPROVED,
            allowed=True,
            reason="Action is within the actor's configured autonomy boundary.",
            requires_owner=False,
        )
