"""Single durable orchestration boundary for AURELIX autonomy."""
from __future__ import annotations

from dataclasses import dataclass, is_dataclass, asdict
import json
import threading
from typing import Any
from uuid import uuid4

from .experiment_runner import ExperimentRunner
from .integrated_engines import (
    AcademyEngine, BusinessEngine, EngineStore, EvaluationEngine,
    ExperimentEngine, InnovationEngine, KnowledgeEngine, OpportunityEngine,
    ResearchEngine,
)
from .knowledge_store import SQLiteKnowledgeRepository
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


class AutonomyFabric:
    """Run the complete research-to-business chain under one durable execution."""

    def __init__(self, store: RuntimeStore | None = None, engine_store: EngineStore | None = None,
                 research: ResearchEngine | None = None, academy: AcademyEngine | None = None,
                 knowledge: KnowledgeEngine | None = None, innovation: InnovationEngine | None = None,
                 experiment: ExperimentEngine | None = None, evaluation: EvaluationEngine | None = None,
                 opportunity: OpportunityEngine | None = None, business: BusinessEngine | None = None) -> None:
        self.store = store or RuntimeStore()
        # Knowledge is stored in the same RuntimeStore database as executions,
        # so research -> learning -> opportunity does not split across stores.
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
        self.experiment_runner = ExperimentRunner(collector=self._collect_observations, on_complete=self._persist_experiment)

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

    def run_claimed(self, claimed: JobRecord) -> AutonomyRun:
        """Execute an already-claimed job without creating a second lifecycle."""
        if claimed.status != "running" or not claimed.worker_id or not claimed.lease_token:
            raise RuntimeError(f"execution is not actively owned: {claimed.job_id}")
        execution_id = claimed.job_id
        objective = str(claimed.payload.get("objective", "")).strip()
        if not objective:
            raise ValueError("research objective is required")

        stop = threading.Event()
        heartbeat = threading.Thread(
            target=self._heartbeat_loop,
            args=(execution_id, claimed.worker_id, claimed.lease_token, stop),
            name=f"aurelix-lease-{execution_id}", daemon=True,
        )
        heartbeat.start()
        self.store.record_audit(execution_id, "autonomy.started", {"objective": objective, "actor": claimed.worker_id})
        try:
            research = self.research.run(objective, self.engines)
            self.store.record_audit(execution_id, "autonomy.research", {
                "evidence_count": len(research.get("evidence", [])),
                "status": research.get("status"),
                "provider_available": research.get("provider_available"),
            })
            academy = self.academy.run(research, self.engines)
            knowledge = self.knowledge.run(academy, self.engines)
            innovation = self.innovation.run(knowledge, self.engines)
            experiment = self.experiment.run(innovation, self.engines)
            if experiment.get("experiment_id"):
                experiment_record = self.engines.experiments[experiment["experiment_id"]]
                experiment_run = self.experiment_runner.execute(experiment_record)
                experiment = {
                    "experiment_id": experiment_record.id,
                    "status": experiment_run.status,
                    "criteria": experiment_record.success_criteria,
                    "result": experiment_record.result,
                }
            evaluation = self.evaluation.run(experiment, self.engines)
            opportunity = self.opportunity.run(evaluation, self.engines)
            business = self.business.run(opportunity, approved=False)
            lifecycle_status = business.get("status") or "completed"
            result = _jsonable({
                "execution_id": execution_id,
                "status": lifecycle_status,
                "research": research, "academy": academy, "knowledge": knowledge,
                "innovation": innovation, "experiment": experiment, "evaluation": evaluation,
                "opportunity": opportunity, "business": business,
            })
            self.store.complete(execution_id, result, worker_id=claimed.worker_id, lease_token=claimed.lease_token)
            self.store.record_audit(execution_id, "autonomy.completed", {"status": result["status"], "worker_id": claimed.worker_id})
            return AutonomyRun(**result)
        except Exception as exc:
            self.store.record_audit(execution_id, "autonomy.failed", {"error": type(exc).__name__})
            raise
        finally:
            stop.set()
            heartbeat.join(timeout=max(1.0, self.store.lease_seconds / 2.0))

    def run(self, objective: str, execution_id: str | None = None) -> AutonomyRun:
        execution_id = execution_id or str(uuid4())
        job = self.store.enqueue("autonomy.run", {"objective": objective}, execution_id=execution_id)
        worker_id = f"autonomy:{execution_id}"
        claimed = self.store.claim(job.job_id, worker_id=worker_id)
        if claimed is None:
            raise RuntimeError(f"autonomy execution is not claimable: {execution_id}")
        try:
            return self.run_claimed(claimed)
        except Exception as exc:
            current = self.store.get(execution_id)
            if current and current.status == "running":
                self.store.finish(
                    execution_id, False, str(exc), retry=False,
                    worker_id=claimed.worker_id, lease_token=claimed.lease_token,
                )
            raise

    def close(self) -> None:
        self.store.close()
