"""Bridge validated capabilities into opportunity candidates.

This module is intentionally proposal-only. It does not authorize or execute
anything; Governor and Runtime remain the only execution boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from .continuous_intelligence import Capability, ContinuousIntelligence


@dataclass(frozen=True)
class OpportunityCandidate:
    opportunity_id: str
    capability_id: str
    title: str
    rationale: str
    status: str = "candidate"
    requires_governor: bool = True


class CapabilityOpportunityBridge:
    """Turn validated capabilities into auditable, non-executable candidates."""

    def __init__(self, intelligence: ContinuousIntelligence) -> None:
        self.intelligence = intelligence
        self.opportunities: dict[str, OpportunityCandidate] = {}
        self._by_capability: dict[str, str] = {}

    def propose(self, capability_id: str, *, title: str | None = None) -> OpportunityCandidate:
        capability = self._require_validated_capability(capability_id)
        existing_id = self._by_capability.get(capability_id)
        if existing_id is not None:
            return self.opportunities[existing_id]

        candidate = OpportunityCandidate(
            opportunity_id=str(uuid4()),
            capability_id=capability.capability_id,
            title=(title or f"Opportunity from capability: {capability.name}").strip(),
            rationale=(
                f"Derived from validated capability '{capability.name}' "
                f"in domain '{capability.domain}'."
            ),
        )
        if not candidate.title:
            raise ValueError("opportunity title is required")
        self.opportunities[candidate.opportunity_id] = candidate
        self._by_capability[capability_id] = candidate.opportunity_id
        return candidate

    def _require_validated_capability(self, capability_id: str) -> Capability:
        try:
            capability = self.intelligence.capabilities[capability_id]
        except KeyError as exc:
            raise KeyError(capability_id) from exc
        if not capability.validated:
            raise ValueError("only validated capabilities can create opportunities")
        return capability
