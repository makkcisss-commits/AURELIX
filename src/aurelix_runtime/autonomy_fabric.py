"""Single durable orchestration boundary for AURELIX autonomy."""
from __future__ import annotations

from dataclasses import dataclass, is_dataclass, asdict
import json
import threading
import time
from typing import Any
from uuid import uuid4

from aurelix_core.adaptive_loop import AdaptiveLoop
from aurelix_core.capability_escalation import CapabilityEscalator
from .experiment_runner import ExperimentRunner
from .integrated_engines import AcademyEngine, BusinessEngine, EngineStore, EvaluationEngine, ExperimentEngine, InnovationEngine, KnowledgeEngine, OpportunityEngine, ResearchEngine
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

    _SUPPORTED_CAPABILITIES = frozenset({"research", "knowledge", "academy", "innovation", "experiment", "evaluation", "opportunity", "business", "economic-analysis"})

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

    def set_experiment_runner(self, runner: ExperimentRunner) -> None:
        if runner is None:
            raise ValueError("experiment runner is required")
        self.experiment_runner = runner

    def _emit(self, topic: str, sender: str, execution_id: str, payload: dict[str, Any], *, causation_id: str | None = None) -> None:
        self.message_fabric.publish(AgentMessage(topic=topic, sender=sender, payload={"execution_id": execution_id, **payload}, correlation_id=execution_id, causation_id=causation_id, idempotency_key=f"{execution_id}:{topic}", provenance={"execution_id": execution_id}))
        self.store.record_audit(execution_id, "fabric.stage", {"topic": topic, "sender": sender})

    def _collect_observations(self, experiment) -> list[dict[str, Any]]:
        with self.store.lock:
            rows = self.store.db.execute("SELECT observation FROM observations WHERE experiment_id=? ORDER BY recorded_at", (experiment.id,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def _persist_experiment(self, experiment, _run) -> None:
        self.engines.experiments[experiment.id] = experiment
        self.engines.persist()

    def _heartbeat_loop(self, execution_id: str, worker_id: str, lease_token: str, stop: threading.Event) -> None:
        interval = max(0.25, min(self.store.lease_seconds / 3.0, 5.0))
        while not stop.wait(interval):
            if not self.store.heartbeat(execution_id, worker_id, lease_token):
                return

    def _save_mission_context(self, execution_id: str, mission: EconomicMission, objective: str, required_capabilities: list[str]) -> None:
        payload = {
            "execution_id": execution_id,
            "mission_id": mission.mission_id,
            "objective": objective,
            "required_capabilities": required_capabilities,
            "state": mission.state.value,
        }
        with self.store.lock, self.store.db:
            self.store.db.execute(
                "INSERT INTO runtime_state(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (f"mission:{execution_id}", json.dumps(payload, sort_keys=True)),
            )

    def _load_mission_context(self, execution_id: str) -> dict[str, Any] | None:
        with self.store.lock:
            row = self.store.db.execute(
                "SELECT value FROM runtime_state WHERE key=?", (f"mission:{execution_id}",)
            ).fetchone()
        if row is None:
            return None
        try:
            return json.loads(row[0])
        except (TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"mission context is corrupt: {execution_id}") from exc

    def _capability_learning_result(self, claimed: JobRecord, mission: EconomicMission, required_capabilities: list[str]) -> AutonomyRun:
        unknown = [
            cap.strip() for cap in required_capabilities
            if cap.strip()
            and cap.strip().casefold() not in self._SUPPORTED_CAPABILITIES
            and not (self.adaptive_loop and self.adaptive_loop.capability_validated(cap))
        ]
        if not unknown:
            raise ValueError("capability learning requested without an unknown capability")
        gaps = []
        if self.capability_escalator is None:
            self.store.record_audit(claimed.job_id, "autonomy.capability_escalation_unavailable", {"capabilities": unknown, "mission_id": mission.mission_id})
            status = "capability_escalation_unavailable"
            academy = {"status": "blocked", "capability_gaps": unknown}
        else:
            for capability in unknown:
                if self.adaptive_loop is not None:
                    _, objective = self.adaptive_loop.block_for_capability(claimed.job_id, capability, reason="required capability is not validated by the runtime", requested_by=claimed.worker_id or "autonomy")
                    gap = self.capability_escalator.gaps[next(gap_id for gap_id, item in self.capability_escalator.gaps.items() if item.study_objective_id == objective.objective_id)]
                else:
                    gap, objective = self.capability_escalator.escalate(capability=capability, reason="required capability is not validated by the runtime", requested_by=claimed.worker_id or "autonomy")
                gaps.append({"gap_id": gap.gap_id, "capability": gap.capability, "study_objective_id": objective.objective_id})
                self.store.record_audit(claimed.job_id, "autonomy.capability_escalated", {**gaps[-1], "mission_id": mission.mission_id})
            status = "capability_learning_required"
            academy = {"status": "learning_required", "capability_gaps": gaps}
        mission.block("required capability is not validated")
        self._save_mission_context(claimed.job_id, mission, str(claimed.payload.get("objective", "")), required_capabilities)
        result = {"execution_id": claimed.job_id, "status": status, "research": {"status": "not_started"}, "academy": academy, "knowledge": {"status": "blocked"}, "innovation": {"status": "blocked"}, "experiment": {"status": "blocked"}, "evaluation": {"status": "blocked"}, "opportunity": {"status": "blocked"}, "business": {"status": "blocked", "reason": "required capability is not validated"}, "mission_id": mission.mission_id}
        self.store.complete(claimed.job_id, result, worker_id=claimed.worker_id, lease_token=claimed.lease_token)
        return AutonomyRun(**result)

    def run_claimed(self, claimed: JobRecord, required_capabilities: list[str] | None = None, mission_id: str | None = None) -> AutonomyRun:
        if claimed.status != "running" or not claimed.worker_id or not claimed.lease_token:
            raise RuntimeError(f"execution is not actively owned: {claimed.job_id}")
        execution_id = claimed.job_id
        objective = str(claimed.payload.get("objective", "")).strip()
        if not objective:
            raise ValueError("research objective is required")
        required_capabilities = required_capabilities or list(claimed.payload.get("required_capabilities", []))
        mission_id = mission_id or str(claimed.payload.get("mission_id", "")).strip() or str(uuid4())
        mission = EconomicMission(objective, source="autonomy", mission_id=mission_id, constraints={"execution_id": execution_id})
        mission.plan(list(DEFAULT_ECONOMIC_TASKS))
        mission.start()
        self._save_mission_context(execution_id, mission, objective, required_capabilities)
        if self.adaptive_loop is not None:
            self.adaptive_loop.register_mission(execution_id, objective, required_capabilities, mission_id=mission_id)
        if required_capabilities:
            unknown = [cap.strip() for cap in required_capabilities if cap.strip() and cap.strip().casefold() not in self._SUPPORTED_CAPABILITIES and not (self.adaptive_loop and self.adaptive_loop.capability_validated(cap))]
            if unknown:
                return self._capability_learning_result(claimed, mission, required_capabilities)

        self._emit("mission.started", "orchestrator", execution_id, {"mission_id": mission.mission_id, "objective": objective})
        stop = threading.Event()
        heartbeat = threading.Thread(target=self._heartbeat_loop, args=(execution_id, claimed.worker_id, claimed.lease_token, stop), name=f"aurelix-lease-{execution_id}", daemon=True)
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
            if lifecycle_status in {"awaiting_measurement", "awaiting_execution", "awaiting_validation", "awaiting_approval", "awaiting_provider"}:
                mission.block(lifecycle_status)
            else:
                mission.complete([{"type": "pipeline_result", "status": lifecycle_status, "verified": lifecycle_status == "completed"}])
            self._save_mission_context(execution_id, mission, objective, required_capabilities)
            self.store.complete(execution_id, result, worker_id=claimed.worker_id, lease_token=claimed.lease_token)
            self.store.record_audit(execution_id, "autonomy.completed", {"status": result["status"], "worker_id": claimed.worker_id, "mission_id": mission.mission_id})
            self._emit("mission.completed", "orchestrator", execution_id, {"mission_id": mission.mission_id, "status": lifecycle_status})
            return AutonomyRun(**result)
        except Exception as exc:
            mission.block(type(exc).__name__)
            self._save_mission_context(execution_id, mission, objective, required_capabilities)
            self._emit("mission.blocked", "orchestrator", execution_id, {"mission_id": mission.mission_id, "reason": type(exc).__name__})
            self.store.record_audit(execution_id, "autonomy.failed", {"error": type(exc).__name__, "mission_id": mission.mission_id})
            raise
        finally:
            stop.set()
            heartbeat.join(timeout=max(1.0, self.store.lease_seconds / 2.0))

    def run(self, objective: str, execution_id: str | None = None, required_capabilities: list[str] | None = None, mission_id: str | None = None) -> AutonomyRun:
        execution_id = execution_id or str(uuid4())
        payload = {"objective": objective, "required_capabilities": required_capabilities or []}
        if mission_id:
            payload["mission_id"] = mission_id
        job = self.store.enqueue("autonomy.run", payload, execution_id=execution_id)
        worker_id = f"autonomy:{execution_id}"
        claimed = self.store.claim(job.job_id, worker_id=worker_id)
        if claimed is None:
            raise RuntimeError(f"autonomy execution is not claimable: {execution_id}")
        try:
            return self.run_claimed(claimed, required_capabilities=required_capabilities, mission_id=mission_id)
        except Exception as exc:
            current = self.store.get(execution_id)
            if current and current.status == "running":
                self.store.finish(execution_id, False, str(exc), retry=False, worker_id=claimed.worker_id, lease_token=claimed.lease_token)
            raise

    def _claim_resume_execution(self, blocked_execution_id: str, mission_id: str) -> str:
        key = f"mission-resume:{mission_id}"
        candidate = f"{mission_id}:resume:{uuid4()}"
        now = time.time()
        lease_until = now + max(1.0, float(self.store.lease_seconds))
        with self.store.lock:
            self.store.db.execute("BEGIN IMMEDIATE")
            try:
                row = self.store.db.execute("SELECT value FROM runtime_state WHERE key=?", (key,)).fetchone()
                if row is not None:
                    state = json.loads(row[0])
                    existing_id = str(state.get("execution_id") or "").strip()
                    phase = state.get("state")
                    existing_job = self.store.get(existing_id) if existing_id else None
                    if phase == "completed" and existing_job is not None:
                        self.store.db.commit()
                        return existing_id
                    if phase == "reserved":
                        existing_lease = state.get("lease_until")
                        if existing_lease is None:
                            self.store.db.commit()
                            raise RuntimeError("mission resume reservation has no lease metadata")
                        try:
                            if float(existing_lease) > now:
                                self.store.db.commit()
                                raise RuntimeError("mission resume already in progress")
                        except (TypeError, ValueError) as exc:
                            self.store.db.commit()
                            raise RuntimeError("mission resume reservation has invalid lease metadata") from exc
                    elif phase == "running":
                        if existing_job is not None and existing_job.status == "completed":
                            self.store.db.commit()
                            return existing_id
                        if existing_job is not None and existing_job.status == "running" and existing_job.lease_until:
                            try:
                                if existing_job.lease_until > self.store._now():
                                    self.store.db.commit()
                                    raise RuntimeError("mission resume already in progress")
                            except ValueError:
                                pass
                    elif phase not in {"completed", "reserved", "running"}:
                        self.store.db.commit()
                        raise RuntimeError(f"invalid mission resume state: {phase}")
                self.store.db.execute(
                    "INSERT INTO runtime_state(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (key, json.dumps({"state": "reserved", "mission_id": mission_id, "blocked_execution_id": blocked_execution_id, "execution_id": candidate, "lease_until": lease_until}, sort_keys=True)),
                )
                self.store.db.commit()
                return candidate
            except Exception:
                self.store.db.rollback()
                raise

    def _mark_resume_running(self, mission_id: str, blocked_execution_id: str, execution_id: str) -> None:
        with self.store.lock, self.store.db:
            row = self.store.db.execute("SELECT value FROM runtime_state WHERE key=?", (f"mission-resume:{mission_id}",)).fetchone()
            if row is None:
                raise RuntimeError("mission resume reservation disappeared")
            state = json.loads(row[0])
            if state.get("execution_id") != execution_id or state.get("blocked_execution_id") != blocked_execution_id:
                raise RuntimeError("mission resume reservation ownership changed")
            state.update({"state": "running", "lease_until": None})
            self.store.db.execute("UPDATE runtime_state SET value=? WHERE key=?", (json.dumps(state, sort_keys=True), f"mission-resume:{mission_id}"))

    def _mark_resume_completed(self, mission_id: str, blocked_execution_id: str, execution_id: str) -> None:
        with self.store.lock, self.store.db:
            row = self.store.db.execute("SELECT value FROM runtime_state WHERE key=?", (f"mission-resume:{mission_id}",)).fetchone()
            if row is None:
                raise RuntimeError("mission resume completion marker disappeared")
            state = json.loads(row[0])
            if state.get("execution_id") != execution_id or state.get("blocked_execution_id") != blocked_execution_id:
                raise RuntimeError("mission resume completion ownership changed")
            state.update({"state": "completed", "lease_until": None})
            self.store.db.execute("UPDATE runtime_state SET value=? WHERE key=?", (json.dumps(state, sort_keys=True), f"mission-resume:{mission_id}"))

    def resume_mission(self, blocked_execution_id: str) -> AutonomyRun:
        """Resume a validated mission with stable mission identity and a new execution attempt."""
        if self.adaptive_loop is None:
            raise RuntimeError("adaptive loop is unavailable")
        context = self._load_mission_context(blocked_execution_id)
        if context is None:
            raise KeyError(blocked_execution_id)
        mission_id = str(context.get("mission_id", "")).strip()
        objective = str(context.get("objective", "")).strip()
        required_capabilities = list(context.get("required_capabilities", []))
        if not mission_id or not objective:
            raise RuntimeError("mission context is incomplete")
        mission = self.adaptive_loop.missions.get(blocked_execution_id)
        if mission is None:
            mission = self.adaptive_loop.restore_mission(
                execution_id=blocked_execution_id,
                mission_id=mission_id,
                objective=objective,
                required_capabilities=required_capabilities,
                blocked=True,
            )
        if not self.adaptive_loop.can_resume(blocked_execution_id):
            raise RuntimeError("required capabilities are not validated")

        resume_execution_id = self._claim_resume_execution(blocked_execution_id, mission_id)
        existing = self.store.get(resume_execution_id)
        if existing is not None and existing.status == "completed":
            result = self.store.get_result(resume_execution_id)
            if result is None:
                raise RuntimeError("completed resume execution has no durable result")
            return AutonomyRun(**result)

        # Critical ordering: durable ownership is claimed before AdaptiveLoop
        # mutation. A concurrent loser therefore cannot change adaptive state.
        self.adaptive_loop.resume_ready(blocked_execution_id)
        self._mark_resume_running(mission_id, blocked_execution_id, resume_execution_id)
        try:
            result = self.run(
                objective,
                execution_id=resume_execution_id,
                required_capabilities=required_capabilities,
                mission_id=mission_id,
            )
            self._mark_resume_completed(mission_id, blocked_execution_id, resume_execution_id)
            return result
        except Exception:
            # The durable job state remains the source of truth. A later resume
            # can reclaim a failed/missing execution without mutating the parent.
            raise

    def close(self) -> None:
        self.store.close()
