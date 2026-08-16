"""Shared adaptive loop connecting mission, learning, evidence and capability state."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .capability_escalation import CapabilityEscalator
from .continuous_intelligence import ContinuousIntelligence, Evidence, EvidenceKind, EvaluationStatus


@dataclass(frozen=True)
class AdaptiveMission:
    execution_id: str
    objective: str
    required_capabilities: tuple[str, ...] = ()
    blocked: bool = False
    capability_gap_ids: tuple[str, ...] = ()
    mission_id: str = ""

    def __post_init__(self) -> None:
        if not self.execution_id.strip() or not self.objective.strip():
            raise ValueError("execution_id and objective are required")
        if not self.mission_id:
            object.__setattr__(self, "mission_id", self.execution_id)


@dataclass
class AdaptiveLoop:
    """One shared coordination boundary for AURELIX's adaptive lifecycle."""
    intelligence: ContinuousIntelligence
    capability_escalator: CapabilityEscalator
    missions: dict[str, AdaptiveMission] = field(default_factory=dict)
    _capability_missions: dict[str, set[str]] = field(default_factory=dict)
    resume_executor: Callable[[AdaptiveMission], Any] | None = field(default=None, repr=False)
    state_persistor: Callable[[str, dict[str, Any]], None] | None = field(default=None, repr=False)
    _persisted_validated_capabilities: set[str] = field(default_factory=set, repr=False)

    def _persist_mission(self, mission: AdaptiveMission) -> None:
        if self.state_persistor is not None:
            self.state_persistor(f"mission:{mission.execution_id}", {
                "execution_id": mission.execution_id, "mission_id": mission.mission_id,
                "objective": mission.objective, "required_capabilities": list(mission.required_capabilities),
                "blocked": mission.blocked, "capability_gap_ids": list(mission.capability_gap_ids),
            })

    def register_mission(self, execution_id: str, objective: str, required_capabilities: list[str] | tuple[str, ...] = (), mission_id: str | None = None) -> AdaptiveMission:
        if not execution_id.strip() or not objective.strip():
            raise ValueError("execution_id and objective are required")
        mission = AdaptiveMission(execution_id, objective, tuple(required_capabilities), mission_id=mission_id or execution_id)
        self.missions[execution_id] = mission
        self._persist_mission(mission)
        return mission

    def restore_mission(self, *, execution_id: str, objective: str, required_capabilities: tuple[str, ...], mission_id: str, blocked: bool, capability_gap_ids: tuple[str, ...] = ()) -> AdaptiveMission:
        mission = AdaptiveMission(execution_id, objective, required_capabilities, blocked=blocked, capability_gap_ids=capability_gap_ids, mission_id=mission_id)
        self.missions[execution_id] = mission
        return mission

    def restore_validated_capability(self, capability: str) -> None:
        if capability.strip():
            self._persisted_validated_capabilities.add(capability.casefold())

    def block_for_capability(self, execution_id: str, capability: str, *, reason: str, requested_by: str) -> tuple[AdaptiveMission, Any]:
        mission = self.missions.get(execution_id)
        if mission is None:
            raise KeyError(execution_id)
        gap, objective = self.capability_escalator.escalate(capability=capability, reason=reason, requested_by=requested_by)
        self._capability_missions.setdefault(capability.casefold(), set()).add(execution_id)
        updated = AdaptiveMission(mission.execution_id, mission.objective, mission.required_capabilities, blocked=True, capability_gap_ids=(*mission.capability_gap_ids, gap.gap_id), mission_id=mission.mission_id)
        self.missions[execution_id] = updated
        self._persist_mission(updated)
        return updated, objective

    def record_evidence(self, *, objective_id: str, kind: EvidenceKind, reference: str, strength: float = 0.5, notes: str = "") -> Evidence:
        return self.intelligence.record_evidence(objective_id=objective_id, kind=kind, reference=reference, strength=strength, notes=notes)

    def validate_learning(self, *, execution_id: str, capability: str, objective_id: str, evaluation_id: str, evidence_refs: tuple[str, ...]) -> Any:
        mission = self.missions.get(execution_id)
        if mission is None:
            raise KeyError(execution_id)
        evaluation = self.intelligence.evaluations.get(evaluation_id)
        if evaluation is None:
            raise KeyError(evaluation_id)
        if evaluation.objective_id != objective_id:
            raise ValueError("evaluation does not belong to objective")
        if evaluation.status is not EvaluationStatus.PASSED:
            raise RuntimeError("learning evaluation did not pass")
        if not evidence_refs or not set(evidence_refs).issubset(evaluation.evidence_refs):
            raise ValueError("capability evidence must be covered by the passed evaluation")
        if capability.casefold() not in {item.casefold() for item in mission.required_capabilities}:
            raise ValueError("capability is not required by mission")
        objective = self.intelligence.objectives.get(objective_id)
        if objective is None:
            raise KeyError(objective_id)
        if capability.casefold() not in {item.casefold() for item in objective.target_competencies}:
            raise ValueError("capability is not a target competency of the learning objective")
        validated = self.intelligence.validate_capability(name=capability, domain=objective.domain, required_competencies=objective.target_competencies, evidence_refs=evidence_refs)
        self._persisted_validated_capabilities.add(capability.casefold())
        if self.state_persistor is not None:
            self.state_persistor(f"capability:{capability.casefold()}", {"capability": capability, "validated": True, "objective_id": objective_id, "evaluation_id": evaluation_id, "evidence_refs": list(evidence_refs)})
        return validated

    def capability_validated(self, capability: str) -> bool:
        normalized = capability.casefold()
        return normalized in self._persisted_validated_capabilities or any(item.name.casefold() == normalized and item.validated for item in self.intelligence.capabilities.values())

    def can_resume(self, execution_id: str) -> bool:
        mission = self.missions.get(execution_id)
        if mission is None:
            raise KeyError(execution_id)
        return all(self.capability_validated(capability) for capability in mission.required_capabilities)

    def set_resume_executor(self, executor: Callable[[AdaptiveMission], Any] | None) -> None:
        self.resume_executor = executor

    def set_state_persistor(self, persistor: Callable[[str, dict[str, Any]], None] | None) -> None:
        self.state_persistor = persistor

    def resume_ready(self, execution_id: str) -> AdaptiveMission:
        mission = self.missions.get(execution_id)
        if mission is None:
            raise KeyError(execution_id)
        if not self.can_resume(execution_id):
            raise RuntimeError("required capabilities are not validated")
        updated = AdaptiveMission(mission.execution_id, mission.objective, mission.required_capabilities, blocked=False, capability_gap_ids=mission.capability_gap_ids, mission_id=mission.mission_id)
        if self.resume_executor is not None:
            self.resume_executor(updated)
        self.missions[execution_id] = updated
        self._persist_mission(updated)
        return updated
