"""Shared adaptive loop connecting mission, learning, evidence and capability state."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

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
    """One shared coordination boundary for AURELIX's adaptive lifecycle.

    It owns coordination state only. Runtime/Governor remain the authorization
    boundary; learning never grants execution authority by itself.

    The optional RuntimeStore is used only for durable mission/capability
    continuity. It does not become an execution authority.
    """

    intelligence: ContinuousIntelligence
    capability_escalator: CapabilityEscalator
    missions: dict[str, AdaptiveMission] = field(default_factory=dict)
    _capability_missions: dict[str, set[str]] = field(default_factory=dict)
    store: Any | None = field(default=None, repr=False)
    _durable_validated_capabilities: dict[str, dict[str, Any]] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self._load_durable_capabilities()

    @staticmethod
    def _normalize_capability(capability: str) -> str:
        normalized = capability.strip().casefold()
        if not normalized:
            raise ValueError("capability is required")
        return normalized

    def _load_durable_capabilities(self) -> None:
        if self.store is None:
            return
        with self.store.lock:
            rows = self.store.db.execute(
                "SELECT key,value FROM runtime_state WHERE key LIKE 'capability-validation:%'"
            ).fetchall()
        for row in rows:
            try:
                payload = json.loads(row["value"])
            except (TypeError, json.JSONDecodeError):
                continue
            if payload.get("validated") is True and str(payload.get("name", "")).strip():
                self._durable_validated_capabilities[
                    self._normalize_capability(str(payload["name"]))
                ] = payload

    def _persist_validated_capability(self, capability: Any) -> None:
        if self.store is None:
            return
        payload = {
            "validated": True,
            "capability_id": capability.capability_id,
            "name": capability.name,
            "domain": capability.domain,
            "required_competencies": list(capability.required_competencies),
            "evidence_refs": list(capability.evidence_refs),
        }
        key = f"capability-validation:{self._normalize_capability(capability.name)}"
        with self.store.lock, self.store.db:
            self.store.db.execute(
                "INSERT INTO runtime_state(key,value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, json.dumps(payload, sort_keys=True)),
            )
        self._durable_validated_capabilities[self._normalize_capability(capability.name)] = payload

    def register_mission(self, execution_id: str, objective: str,
                         required_capabilities: list[str] | tuple[str, ...] = (),
                         mission_id: str | None = None) -> AdaptiveMission:
        if not execution_id.strip() or not objective.strip():
            raise ValueError("execution_id and objective are required")
        mission = AdaptiveMission(
            execution_id,
            objective,
            tuple(required_capabilities),
            mission_id=mission_id or execution_id,
        )
        self.missions[execution_id] = mission
        for capability in mission.required_capabilities:
            self._capability_missions.setdefault(self._normalize_capability(capability), set()).add(execution_id)
        return mission

    def restore_mission(self, *, execution_id: str, mission_id: str, objective: str,
                        required_capabilities: list[str] | tuple[str, ...] = (),
                        blocked: bool = True,
                        capability_gap_ids: list[str] | tuple[str, ...] = ()) -> AdaptiveMission:
        """Rehydrate durable mission identity without granting execution authority."""
        mission = AdaptiveMission(
            execution_id=execution_id,
            mission_id=mission_id,
            objective=objective,
            required_capabilities=tuple(required_capabilities),
            blocked=blocked,
            capability_gap_ids=tuple(capability_gap_ids),
        )
        self.missions[execution_id] = mission
        for capability in mission.required_capabilities:
            self._capability_missions.setdefault(self._normalize_capability(capability), set()).add(execution_id)
        return mission

    def block_for_capability(self, execution_id: str, capability: str,
                             *, reason: str, requested_by: str) -> tuple[AdaptiveMission, Any]:
        mission = self.missions.get(execution_id)
        if mission is None:
            raise KeyError(execution_id)
        gap, objective = self.capability_escalator.escalate(
            capability=capability, reason=reason, requested_by=requested_by,
        )
        key = self._normalize_capability(capability)
        self._capability_missions.setdefault(key, set()).add(execution_id)
        updated = AdaptiveMission(
            mission.execution_id, mission.objective, mission.required_capabilities,
            blocked=True, capability_gap_ids=(*mission.capability_gap_ids, gap.gap_id),
            mission_id=mission.mission_id,
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

    def validate_learning(self, *, execution_id: str, capability: str,
                          objective_id: str, evaluation_id: str,
                          evidence_refs: tuple[str, ...]) -> Any:
        """Convert Academy learning into an operational capability only after a pass."""
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
        normalized = self._normalize_capability(capability)
        if normalized not in {self._normalize_capability(item) for item in mission.required_capabilities}:
            raise ValueError("capability is not required by mission")
        objective = self.intelligence.objectives.get(objective_id)
        if objective is None:
            raise KeyError(objective_id)
        if normalized not in {self._normalize_capability(item) for item in objective.target_competencies}:
            raise ValueError("capability is not a target competency of the learning objective")
        validated = self.intelligence.validate_capability(
            name=capability,
            domain=objective.domain,
            required_competencies=objective.target_competencies,
            evidence_refs=evidence_refs,
        )
        self._persist_validated_capability(validated)
        return validated

    def capability_validated(self, capability: str) -> bool:
        normalized = self._normalize_capability(capability)
        if any(item.name.casefold() == normalized and item.validated
               for item in self.intelligence.capabilities.values()):
            return True
        return normalized in self._durable_validated_capabilities

    def can_resume(self, execution_id: str) -> bool:
        mission = self.missions.get(execution_id)
        if mission is None:
            raise KeyError(execution_id)
        return all(self.capability_validated(capability) for capability in mission.required_capabilities)

    def resume_ready(self, execution_id: str) -> AdaptiveMission:
        mission = self.missions.get(execution_id)
        if mission is None:
            raise KeyError(execution_id)
        if not self.can_resume(execution_id):
            raise RuntimeError("required capabilities are not validated")
        updated = AdaptiveMission(
            mission.execution_id, mission.objective, mission.required_capabilities,
            blocked=False, capability_gap_ids=mission.capability_gap_ids,
            mission_id=mission.mission_id,
        )
        self.missions[execution_id] = updated
        return updated
