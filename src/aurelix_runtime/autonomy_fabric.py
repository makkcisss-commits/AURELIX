"""Single durable orchestration boundary for AURELIX autonomy."""
from __future__ import annotations
from dataclasses import dataclass, is_dataclass, asdict
import json, threading
from typing import Any
from uuid import uuid4
from .experiment_runner import ExperimentRunner
from .integrated_engines import AcademyEngine, BusinessEngine, EngineStore, EvaluationEngine, ExperimentEngine, InnovationEngine, KnowledgeEngine, OpportunityEngine, ResearchEngine
from .knowledge_store import SQLiteKnowledgeRepository
from .message_fabric import AgentMessage, MessageFabric
from .mission_contracts import DEFAULT_ECONOMIC_TASKS, EconomicMission
from .persistence import JobRecord, RuntimeStore
from .research_provider import HttpResearchProvider

def _jsonable(value: Any) -> Any:
    if is_dataclass(value): return _jsonable(asdict(value))
    if isinstance(value, dict): return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [_jsonable(v) for v in value]
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
    def __init__(self, store=None, engine_store=None, research=None, academy=None, knowledge=None, innovation=None, experiment=None, evaluation=None, opportunity=None, business=None, message_fabric=None, capability_escalator=None):
        self.store = store or RuntimeStore()
        self.message_fabric = message_fabric or MessageFabric()
        self.knowledge_repository = SQLiteKnowledgeRepository(self.store)
        self.engines = engine_store or EngineStore(runtime_store=self.store, knowledge_repository=self.knowledge_repository)
        self.research = research or ResearchEngine(provider=HttpResearchProvider.from_env())
        self.academy = academy or AcademyEngine()
        self.knowledge = knowledge or KnowledgeEngine()
        self.innovation = innovation or InnovationEngine()
        self.experiment = experiment or ExperimentEngine()
        self.evaluation = evaluation or EvaluationEngine()
        self.opportunity = opportunity or OpportunityEngine()
        self.business = business or BusinessEngine(require_approval=True)
        self.capability_escalator = capability_escalator
        self.experiment_runner = ExperimentRunner(collector=self._collect_observations, on_complete=self._persist_experiment)

    def _emit(self, topic, sender, execution_id, payload, *, causation_id=None):
        self.message_fabric.publish(AgentMessage(topic=topic, sender=sender, payload={"execution_id": execution_id, **payload}, correlation_id=execution_id, causation_id=causation_id, idempotency_key=f"{execution_id}:{topic}", provenance={"execution_id": execution_id}))
        self.store.record_audit(execution_id, "fabric.stage", {"topic": topic, "sender": sender})

    def _collect_observations(self, experiment):
        with self.store.lock:
            rows = self.store.db.execute("SELECT observation FROM observations WHERE experiment_id=? ORDER BY recorded_at", (experiment.id,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def _persist_experiment(self, experiment, _run):
        self.engines.experiments[experiment.id] = experiment
        self.engines.persist()

    def _heartbeat_loop(self, execution_id, worker_id, lease_token, stop):
        interval = max(0.25, min(self.store.lease_seconds / 3.0, 5.0))
        while not stop.wait(interval):
            if not self.store.heartbeat(execution_id, worker_id, lease_token): return

    def _capability_preflight(self, claimed: JobRecord, execution_id: str) -> AutonomyRun | None:
        requested = tuple(dict.fromkeys(str(x).strip() for x in claimed.payload.get("required_capabilities", []) if str(x).strip()))
        if not requested or self.capability_escalator is None:
            return None
        known = {"web-research", "knowledge-synthesis", "innovation", "experimentation", "evaluation", "opportunity-analysis", "business-planning", "economic-attribution"}
        missing = [capability for capability in requested if capability not in known]
        if not missing:
            return None
        gaps = []
        for capability in missing:
            gap, objective = self.capability_escalator.escalate(capability=capability, reason="required capability is not validated for autonomous execution", requested_by=claimed.worker_id or "autonomy")
            gaps.append({"gap_id": gap.gap_id, "capability": gap.capability, "study_objective_id": objective.objective_id})
        result = {"execution_id": execution_id, "status": "capability_learning_required", "research": {"status": "blocked"}, "academy": {"status": "learning_required", "capability_gaps": gaps}, "knowledge": {}, "innovation": {}, "experiment": {}, "evaluation": {}, "opportunity": {}, "business": {"status": "blocked"}, "mission_id": ""}
        self.store.complete(execution_id, result, worker_id=claimed.worker_id, lease_token=claimed.lease_token)
        self.store.record_audit(execution_id, "autonomy.capability_escalated", {"missing": missing, "gaps": gaps})
        return AutonomyRun(**result)

    def run_claimed(self, claimed: JobRecord) -> AutonomyRun:
        if claimed.status != "running" or not claimed.worker_id or not claimed.lease_token: raise RuntimeError(f"execution is not actively owned: {claimed.job_id}")
        execution_id = claimed.job_id
        objective = str(claimed.payload.get("objective", "")).strip()
        if not objective: raise ValueError("research objective is required")
        preflight = self._capability_preflight(claimed, execution_id)
        if preflight is not None: return preflight
        mission = EconomicMission(objective, source="autonomy", constraints={"execution_id": execution_id})
        mission.plan(list(DEFAULT_ECONOMIC_TASKS)); mission.start()
        self._emit("mission.started", "orchestrator", execution_id, {"mission_id": mission.mission_id, "objective": objective})
        stop = threading.Event(); heartbeat = threading.Thread(target=self._heartbeat_loop, args=(execution_id, claimed.worker_id, claimed.lease_token, stop), name=f"aurelix-lease-{execution_id}", daemon=True); heartbeat.start()
        self.store.record_audit(execution_id, "autonomy.started", {"objective": objective, "actor": claimed.worker_id, "mission_id": mission.mission_id})
        try:
            research = self.research.run(objective, self.engines); self._emit("research.completed", "research", execution_id, {"status": research.get("status"), "evidence_count": len(research.get("evidence", []))})
            academy = self.academy.run(research, self.engines); self._emit("academy.completed", "academy", execution_id, {"status": academy.get("status")})
            knowledge = self.knowledge.run(academy, self.engines); self._emit("knowledge.completed", "knowledge", execution_id, {"status": knowledge.get("status")})
            innovation = self.innovation.run(knowledge, self.engines); self._emit("innovation.completed", "innovation", execution_id, {"status": innovation.get("status")})
            experiment = self.experiment.run(innovation, self.engines)
            if experiment.get("experiment_id"):
                record = self.engines.experiments[experiment["experiment_id"]]; run = self.experiment_runner.execute(record); experiment = {"experiment_id": record.id, "status": run.status, "criteria": record.success_criteria, "result": record.result}
            self._emit("experiment.completed", "experiment", execution_id, {"status": experiment.get("status"), "experiment_id": experiment.get("experiment_id")})
            evaluation = self.evaluation.run(experiment, self.engines); self._emit("evaluation.completed", "validation", execution_id, {"status": evaluation.get("status")})
            opportunity = self.opportunity.run(evaluation, self.engines); self._emit("opportunity.completed", "opportunity", execution_id, {"status": opportunity.get("status")})
            business = self.business.run(opportunity, approved=False); self._emit("business.completed", "business", execution_id, {"status": business.get("status"), "approved": False})
            lifecycle_status = business.get("status") or "completed"
            result = _jsonable({"execution_id": execution_id, "status": lifecycle_status, "research": research, "academy": academy, "knowledge": knowledge, "innovation": innovation, "experiment": experiment, "evaluation": evaluation, "opportunity": opportunity, "business": business, "mission_id": mission.mission_id})
            mission.complete([{"type": "pipeline_result", "status": lifecycle_status, "verified": lifecycle_status == "completed"}]); self.store.complete(execution_id, result, worker_id=claimed.worker_id, lease_token=claimed.lease_token); self.store.record_audit(execution_id, "autonomy.completed", {"status": result["status"], "worker_id": claimed.worker_id, "mission_id": mission.mission_id}); self._emit("mission.completed", "orchestrator", execution_id, {"mission_id": mission.mission_id, "status": lifecycle_status})
            return AutonomyRun(**result)
        except Exception as exc:
            mission.block(type(exc).__name__); self._emit("mission.blocked", "orchestrator", execution_id, {"mission_id": mission.mission_id, "reason": type(exc).__name__}); self.store.record_audit(execution_id, "autonomy.failed", {"error": type(exc).__name__, "mission_id": mission.mission_id}); raise
        finally:
            stop.set(); heartbeat.join(timeout=max(1.0, self.store.lease_seconds / 2.0))

    def run(self, objective: str, execution_id: str | None = None, required_capabilities: list[str] | None = None) -> AutonomyRun:
        execution_id = execution_id or str(uuid4())
        job = self.store.enqueue("autonomy.run", {"objective": objective, "required_capabilities": required_capabilities or []}, execution_id=execution_id)
        worker_id = f"autonomy:{execution_id}"; claimed = self.store.claim(job.job_id, worker_id=worker_id)
        if claimed is None: raise RuntimeError(f"autonomy execution is not claimable: {execution_id}")
        try: return self.run_claimed(claimed)
        except Exception as exc:
            current = self.store.get(execution_id)
            if current and current.status == "running": self.store.finish(execution_id, False, str(exc), retry=False, worker_id=claimed.worker_id, lease_token=claimed.lease_token)
            raise

    def close(self): self.store.close()
