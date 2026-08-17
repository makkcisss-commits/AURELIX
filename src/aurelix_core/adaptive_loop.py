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


@dataclass
class AdaptiveLoop:
    """One shared coordination boundary for AURELIX's adaptive lifecycle.

    It owns coordination state only. Runtime/Governor remain the authorization
    boundary; learning never grants execution authority by itself.

    Validated capability facts are also persisted when a durable RuntimeStore is
    supplied. This keeps the minimum fact required for safe resume across
    process restart without making the in-memory intelligence registry itself an
    authority for execution.
    """

    intelligence: ContinuousIntelligence
    capability_escalator: CapabilityEscalator
    missions: dict[str, AdaptiveMission] = field(default_factory=dict)
    _capability_missions: dict[str, set[str]] = field(default_factory=dict)
    durable_store: Any | None = None
    _durable_validated_capabilities: set[str] = field(default_factory=set, init=False, repr=False)

    _CAPABILITY_STATE_KEY = "adaptive.validated_capabilities"

    def __post_init__(self) -> None:
        self._load_durable_capabilities()

    def _load_durable_capabilities(self) -> None:
        if self.durable_store is None:
            return
        with self.durable_store.lock:
            row = self.durable_store.db.execute(
                "SELECT value FROM runtime_state WHERE key=?",
                (self._CAPABILITY_STATE_KEY,),
            ).fetchone()
        if row is None:
            return
        data = json.loads(row[0])
        if not isinstance(data, list):
            raise RuntimeError("invalid durable capability state")
        self._durable_validated_capabilities = {
            str(item).strip().casefold() for item in data if str(item).strip()
        }

    def _persist_validated_capability(self, capability: str) -> None:
        normalized = capability.strip().casefold()
        if not normalized:
            raise ValueError("capability is required")
        self._durable_validated_capabilities.add(normalized)
        if self.durable_store is None:
            return
        with self.durable_store.lock:
            self.durable_store.db.execute("BEGIN IMMEDIATE")
            try:
                self.durable_store.db.execute(
                    "INSERT INTO runtime_state(key,value) VALUES(?,?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (
                        self._CAPABILITY_STATE_KEY,
                        json.dumps(sorted(self._durable_validated_capabilities)),
                    ),
                )
                self.durable_store.db.commit()
            except Exception:
                self.durable_store.db.rollback()
                raise

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
        if capability.casefold() not in {item.casefold() for item in mission.required_capabilities}:
            raise ValueError("capability is not required by mission")
        objective = self.intelligence.objectives.get(objective_id)
        if objective is None:
            raise KeyError(objective_id)
        if capability.casefold() not in {item.casefold() for item in objective.target_competencies}:
            raise ValueError("capability is not a target competency of the learning objective")
        validated = self.intelligence.validate_capability(
            name=capability,
            domain=objective.domain,
            required_competencies=objective.target_competencies,
            evidence_refs=evidence_refs,
        )
        self._persist_validated_capability(capability)
        return validated

    def capability_validated(self, capability: str) -> bool:
        normalized = capability.casefold()
        return (
            normalized in self._durable_validated_capabilities
            or any(item.name.casefold() == normalized and item.validated
                   for item in self.intelligence.capabilities.values())
        )

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
