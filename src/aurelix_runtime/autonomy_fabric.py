"""Single durable orchestration boundary for AURELIX autonomy."""
from __future__ import annotations

from dataclasses import dataclass, is_dataclass, asdict
import json
import threading
from typing import Any
from uuid import uuid4

from aurelix_core.adaptive_loop import AdaptiveLoop
from aurelix_core.capability_escalation import CapabilityEscalator
from .experiment_runner import ExperimentRunner
from .integrated_engines import (
    AcademyEngine, BusinessEngine, EngineStore, EvaluationEngine,
    ExperimentEngine, InnovationEngine, KnowledgeEngine, OpportunityEngine,
    ResearchEngine,
)
from .knowledge_store import SQLiteKnowledgeRepository
from .message_fabric import AgentMessage, MessageFabric
from .mission_contracts import DEFAULT_ECONOMIC_TASKS, EconomicMission
from .persistence import JobRecord, RuntimeStore
from .research_provider import HttpResearchProvider


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


@dataclass(frozen=True)
class AutonomyRun:
    execution_id: str
    status: str
    research: dict[str, Any]
    academy: dict[str, Any]
    knowledge: dict[str, Any]
    innovation: dict[str, Any]
    experiment: dict[str, Any]
    evaluation: dict[str, Any]
    opportunity: dict[str, Any]
    business: dict[str, Any]
    mission_id: str = ""


class AutonomyFabric:
    """Run the complete research-to-business chain under one durable execution."""

    _SUPPORTED_CAPABILITIES = frozenset({
        "research", "knowledge", "academy", "innovation", "experiment",
        "evaluation", "opportunity", "business", "economic-analysis",
    })

    def __init__(self, store: RuntimeStore | None = None, engine_store: EngineStore | None = None,
                 research: ResearchEngine | None = None, academy: AcademyEngine | None = None,
                 knowledge: KnowledgeEngine | None = None, innovation: InnovationEngine | None = None,
                 experiment: ExperimentEngine | None = None, evaluation: EvaluationEngine | None = None,
                 opportunity: OpportunityEngine | None = None, business: BusinessEngine | None = None,
                 message_fabric: MessageFabric | None = None,
                 capability_escalator: CapabilityEscalator | None = None,
                 adaptive_loop: AdaptiveLoop | None = None,
                 experiment_runner: ExperimentRunner | None = None) -> None:
        self.store = store or RuntimeStore()
        self.message_fabric = message_fabric or MessageFabric()
        self.knowledge_repository = SQLiteKnowledgeRepository(self.store)
        self.engines = engine_store or EngineStore(runtime_store=self.store, knowledge_repository=self.knowledge_repository)
        configured_provider = HttpResearchProvider.from_env()
        self.research = research or ResearchEngine(provider=configured_provider)
        self.academy = academy or AcademyEngine()
        self.knowledge = knowledge or KnowledgeEngine()
        self.innovation = innovation or InnovationEngine()
        self.experiment = experiment or ExperimentEngine()
        self.evaluation = evaluation or EvaluationEngine()
        self.opportunity = opportunity or OpportunityEngine()
        self.business = business or BusinessEngine(require_approval=True)
        self.capability_escalator = capability_escalator
        self.adaptive_loop = adaptive_loop
        self.experiment_runner = experiment_runner or ExperimentRunner(collector=self._collect_observations, on_complete=self._persist_experiment)

    def _emit(self, topic: str, sender: str, execution_id: str, payload: dict[str, Any], *, causation_id: str | None = None) -> None:
        self.message_fabric.publish(AgentMessage(
            topic=topic,
            sender=sender,
            payload={"execution_id": execution_id, **payload},
            correlation_id=execution_id,
            causation_id=causation_id,
            idempotency_key=f"{execution_id}:{topic}",
            provenance={"execution_id": execution_id},
        ))
        self.store.record_audit(execution_id, "fabric.stage", {"topic": topic, "sender": sender})

    def _collect_observations(self, experiment) -> list[dict[str, Any]]:
        with self.store.lock:
            rows = self.store.db.execute(
                "SELECT observation FROM observations WHERE experiment_id=? ORDER BY recorded_at",
                (experiment.id,),
            ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def _persist_experiment(self, experiment, _run) -> None:
        self.engines.experiments[experiment.id] = experiment
        self.engines.persist()

    def _heartbeat_loop(self, execution_id: str, worker_id: str, lease_token: str, stop: threading.Event) -> None:
        interval = max(0.25, min(self.store.lease_seconds / 3.0, 5.0))
        while not stop.wait(interval):
            if not self.store.heartbeat(execution_id, worker_id, lease_token):
                return

    def _capability_learning_result(self, claimed: JobRecord, required_capabilities: list[str]) -> AutonomyRun:
        unknown = [cap.strip() for cap in required_capabilities if cap.strip() and cap.strip().casefold() not in self._SUPPORTED_CAPABILITIES]
        if not unknown:
            raise ValueError("capability learning requested without an unknown capability")
        gaps = []
        if self.capability_escalator is None:
            self.store.record_audit(claimed.job_id, "autonomy.capability_escalation_unavailable", {"capabilities": unknown})
            status = "capability_escalation_unavailable"
            academy = {"status": "blocked", "capability_gaps": unknown}
        else:
            for capability in unknown:
                if self.adaptive_loop is not None:
                    _, objective = self.adaptive_loop.block_for_capability(
                        claimed.job_id, capability,
                        reason="required capability is not validated by the runtime",
                        requested_by=claimed.worker_id or "autonomy",
                    )
                    gap = self.capability_escalator.gaps[next(
                        gap_id for gap_id, item in self.capability_escalator.gaps.items()
                        if item.study_objective_id == objective.objective_id
                    )]
                else:
                    gap, objective = self.capability_escalator.escalate(
                        capability=capability,
                        reason="required capability is not validated by the runtime",
                        requested_by=claimed.worker_id or "autonomy",
                    )
                gaps.append({"gap_id": gap.gap_id, "capability": gap.capability, "study_objective_id": objective.objective_id})
                self.store.record_audit(claimed.job_id, "autonomy.capability_escalated", gaps[-1])
            status = "capability_learning_required"
            academy = {"status": "learning_required", "capability_gaps": gaps}
        result = {
            "execution_id": claimed.job_id,
            "status": status,
            "research": {"status": "not_started"},
            "academy": academy,
            "knowledge": {"status": "blocked"},
            "innovation": {"status": "blocked"},
            "experiment": {"status": "blocked"},
            "evaluation": {"status": "blocked"},
            "opportunity": {"status": "blocked"},
            "business": {"status": "blocked", "reason": "required capability is not validated"},
            "mission_id": "",
        }
        self.store.complete(claimed.job_id, result, worker_id=claimed.worker_id, lease_token=claimed.lease_token)
        return AutonomyRun(**result)

    def run_claimed(self, claimed: JobRecord, required_capabilities: list[str] | None = None) -> AutonomyRun:
        """Execute an already-claimed job without creating a second lifecycle."""
        if claimed.status != "running" or not claimed.worker_id or not claimed.lease_token:
            raise RuntimeError(f"execution is not actively owned: {claimed.job_id}")
        execution_id = claimed.job_id
        objective = str(claimed.payload.get("objective", "")).strip()
        if not objective:
            raise ValueError("research objective is required")
        required_capabilities = required_capabilities or list(claimed.payload.get("required_capabilities", []))
        if self.adaptive_loop is not None:
            self.adaptive_loop.register_mission(execution_id, objective, required_capabilities)
        if required_capabilities:
            unknown = [cap.strip() for cap in required_capabilities if cap.strip() and cap.strip().casefold() not in self._SUPPORTED_CAPABILITIES]
            if unknown:
                return self._capability_learning_result(claimed, required_capabilities)

        mission = EconomicMission(objective, source="autonomy", constraints={"execution_id": execution_id})
        mission.plan(list(DEFAULT_ECONOMIC_TASKS))
        mission.start()
        self._emit("mission.started", "orchestrator", execution_id, {"mission_id": mission.mission_id, "objective": objective})

        stop = threading.Event()
        heartbeat = threading.Thread(
            target=self._heartbeat_loop,
            args=(execution_id, claimed.worker_id, claimed.lease_token, stop),
            name=f"aurelix-lease-{execution_id}", daemon=True,
        )
        heartbeat.start()
        self.store.record_audit(execution_id, "autonomy.started", {"objective": objective, "actor": claimed.worker_id, "mission_id": mission.mission_id})
        try:
            research = self.research.run(objective, self.engines)
            self._emit("research.completed", "research", execution_id, {"status": research.get("status"), "evidence_count": len(research.get("evidence", []))})
            academy = self.academy.run(research, self.engines)
            self._emit("academy.completed", "academy", execution_id, {"status": academy.get("status")})
            knowledge = self.knowledge.run(academy, self.engines)
            self._emit("knowledge.completed", "knowledge", execution_id, {"status": knowledge.get("status")})
            innovation = self.innovation.run(knowledge, self.engines)
            self._emit("innovation.completed", "innovation", execution_id, {"status": innovation.get("status")})
            experiment = self.experiment.run(innovation, self.engines)
            if experiment.get("experiment_id"):
                experiment_record = self.engines.experiments[experiment["experiment_id"]]
                experiment_run = self.experiment_runner.execute(experiment_record)
                self.engines.experiments[experiment_record.id] = experiment_record
                self.engines.persist()
                experiment = {"experiment_id": experiment_record.id, "status": experiment_run.status, "criteria": experiment_record.success_criteria, "result": experiment_record.result}
            self._emit("experiment.completed", "experiment", execution_id, {"status": experiment.get("status"), "experiment_id": experiment.get("experiment_id")})
            evaluation = self.evaluation.run(experiment, self.engines)
            self._emit("evaluation.completed", "validation", execution_id, {"status": evaluation.get("status")})
            opportunity = self.opportunity.run(evaluation, self.engines)
            self._emit("opportunity.completed", "opportunity", execution_id, {"status": opportunity.get("status")})
            business = self.business.run(opportunity, approved=False)
            self._emit("business.completed", "business", execution_id, {"status": business.get("status"), "approved": False})
            lifecycle_status = business.get("status") or "completed"
            result = _jsonable({"execution_id": execution_id, "status": lifecycle_status, "research": research, "academy": academy, "knowledge": knowledge, "innovation": innovation, "experiment": experiment, "evaluation": evaluation, "opportunity": opportunity, "business": business, "mission_id": mission.mission_id})
            mission.complete([{"type": "pipeline_result", "status": lifecycle_status, "verified": lifecycle_status == "completed"}])
            self.store.complete(execution_id, result, worker_id=claimed.worker_id, lease_token=claimed.lease_token)
            self.store.record_audit(execution_id, "autonomy.completed", {"status": result["status"], "worker_id": claimed.worker_id, "mission_id": mission.mission_id})
            self._emit("mission.completed", "orchestrator", execution_id, {"mission_id": mission.mission_id, "status": lifecycle_status})
            return AutonomyRun(**result)
        except Exception as exc:
            mission.block(type(exc).__name__)
            self._emit("mission.blocked", "orchestrator", execution_id, {"mission_id": mission.mission_id, "reason": type(exc).__name__})
            self.store.record_audit(execution_id, "autonomy.failed", {"error": type(exc).__name__, "mission_id": mission.mission_id})
            raise
        finally:
            stop.set()
            heartbeat.join(timeout=max(1.0, self.store.lease_seconds / 2.0)
)

    def run(self, objective: str, execution_id: str | None = None, required_capabilities: list[str] | None = None) -> AutonomyRun:
        execution_id = execution_id or str(uuid4())
        job = self.store.enqueue("autonomy.run", {"objective": objective, "required_capabilities": required_capabilities or []}, execution_id=execution_id)
        worker_id = f"autonomy:{execution_id}"
        claimed = self.store.claim(job.job_id, worker_id=worker_id)
        if claimed is None:
            raise RuntimeError(f"autonomy execution is not claimable: {execution_id}")
        try:
            return self.run_claimed(claimed, required_capabilities=required_capabilities)
        except Exception as exc:
            current = self.store.get(execution_id)
            if current and current.status == "running":
                self.store.finish(execution_id, False, str(exc), retry=False, worker_id=claimed.worker_id, lease_token=claimed.lease_token)
            raise

    def close(self) -> None:
        self.store.close()
