"""Shared adaptive loop connecting mission, learning, evidence and capability state."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .capability_escalation import CapabilityEscalator
from .continuous_intelligence import ContinuousIntelligence, Evidence, EvidenceKind


@dataclass(frozen=True)
class AdaptiveMission:
    execution_id: str
    objective: str
    required_capabilities: tuple[str, ...] = ()
    blocked: bool = False
    capability_gap_ids: tuple[str, ...] = ()


@dataclass
class AdaptiveLoop:
    """One shared coordination boundary for AURELIX's adaptive lifecycle.

    It owns coordination state only. Runtime/Governor remain the authorization
    boundary; learning never grants execution authority by itself.
    """

    intelligence: ContinuousIntelligence
    capability_escalator: CapabilityEscalator
    missions: dict[str, AdaptiveMission] = field(default_factory=dict)
    _capability_missions: dict[str, set[str]] = field(default_factory=dict)

    def register_mission(self, execution_id: str, objective: str,
                         required_capabilities: list[str] | tuple[str, ...] = ()) -> AdaptiveMission:
        if not execution_id.strip() or not objective.strip():
            raise ValueError("execution_id and objective are required")
        mission = AdaptiveMission(execution_id, objective, tuple(required_capabilities))
        self.missions[execution_id] = mission
        return mission

    def block_for_capability(self, execution_id: str, capability: str,
                             *, reason: str, requested_by: str) -> tuple[AdaptiveMission, Any]:
        mission = self.missions.get(execution_id)
        if mission is None:
            raise KeyError(execution_id)
        gap, objective = self.capability_escalator.escalate(
            capability=capability, reason=reason, requested_by=requested_by,
        )
        self._capability_missions.setdefault(capability.casefold(), set()).add(execution_id)
        updated = AdaptiveMission(
            mission.execution_id, mission.objective, mission.required_capabilities,
            blocked=True, capability_gap_ids=(*mission.capability_gap_ids, gap.gap_id),
        )
        self.missions[execution_id] = updated
        return updated, objective

    def record_evidence(self, *, objective_id: str, kind: EvidenceKind,
                        reference: str, strength: float = 0.5,
                        notes: str = "") -> Evidence:
        return self.intelligence.record_evidence(
            objective_id=objective_id, kind=kind, reference=reference,
            strength=strength, notes=notes,
        )

    def capability_validated(self, capability: str) -> bool:
        normalized = capability.casefold()
        return any(item.name.casefold() == normalized and item.validated
                   for item in self.intelligence.capabilities.values())

    def can_resume(self, execution_id: str) -> bool:
        mission = self.missions.get(execution_id)
        if mission is None:
            raise KeyError(execution_id)
        return all(self.capability_validated(capability)
                   for capability in mission.required_capabilities)

    def resume_ready(self, execution_id: str) -> AdaptiveMission:
        mission = self.missions.get(execution_id)
        if mission is None:
            raise KeyError(execution_id)
        if not self.can_resume(execution_id):
            raise RuntimeError("required capabilities are not validated")
        updated = AdaptiveMission(
            mission.execution_id, mission.objective, mission.required_capabilities,
            blocked=False, capability_gap_ids=mission.capability_gap_ids,
        )
        self.missions[execution_id] = updated
        return updated
