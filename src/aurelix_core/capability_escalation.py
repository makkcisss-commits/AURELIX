"""Capability-gap escalation from execution to the Learning Academy."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from .continuous_intelligence import ContinuousIntelligence, StudyObjective


@dataclass(frozen=True)
class CapabilityGap:
    gap_id: str
    capability: str
    reason: str
    requested_by: str
    study_objective_id: str


class CapabilityEscalator:
    """Turn unknown capabilities into traceable Academy work, never fake success."""

    def __init__(self, intelligence: ContinuousIntelligence) -> None:
        self.intelligence = intelligence
        self.gaps: dict[str, CapabilityGap] = {}
        self._by_key: dict[tuple[str, str], str] = {}

    def escalate(self, *, capability: str, reason: str, requested_by: str,
                 priority: float = 0.8) -> tuple[CapabilityGap, StudyObjective]:
        capability, reason, requested_by = capability.strip(), reason.strip(), requested_by.strip()
        if not capability or not reason or not requested_by:
            raise ValueError("capability, reason and requested_by are required")
        if not 0 <= priority <= 1:
            raise ValueError("priority must be between 0 and 1")
        key = (capability.casefold(), reason.casefold())
        existing = self._by_key.get(key)
        if existing is not None:
            gap = self.gaps[existing]
            return gap, self.intelligence.objectives[gap.study_objective_id]
        objective = self.intelligence.propose_objective(
            domain="capability-development",
            title=f"Learn capability: {capability}",
            question=f"How can AURELIX perform '{capability}' safely and reliably? Current gap: {reason}",
            target_competencies=(capability,),
            priority=priority,
        )
        gap = CapabilityGap(str(uuid4()), capability, reason, requested_by, objective.objective_id)
        self.gaps[gap.gap_id] = gap
        self._by_key[key] = gap.gap_id
        return gap, objective
