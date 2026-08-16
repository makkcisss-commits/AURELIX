"""Single connected enterprise loop for AURELIX."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable

from aurelix_core.governor import Governor
from aurelix_core.models import ActionClass, Actor, AutonomyLevel, DecisionRequest
from .integrated_engines import EngineStore, Experiment

@dataclass
class EnterpriseCycle:
    objective: str
    research: dict[str, Any]
    academy: dict[str, Any]
    knowledge: dict[str, Any]
    innovation: dict[str, Any]
    experiment: dict[str, Any]
    evaluation: dict[str, Any]
    opportunity: dict[str, Any]
    business: dict[str, Any]
    @property
    def status(self) -> str:
        return str(self.business.get("status") or self.opportunity.get("status") or self.evaluation.get("reason", "unknown"))

class EnterpriseLoop:
    """Canonical orchestration boundary with a mandatory Governor gate."""
    def __init__(self, *, runtime_store, knowledge_repository, research, academy, knowledge_engine, innovation, experiment, evaluation, opportunity, business, governor: Governor, experiment_submitter: Callable[[Any], str] | None = None):
        if governor is None:
            raise ValueError("enterprise loop requires the canonical governor")
        self.runtime_store = runtime_store
        self.store = EngineStore(runtime_store, knowledge_repository)
        self.research = research; self.academy = academy; self.knowledge_engine = knowledge_engine
        self.innovation = innovation; self.experiment = experiment; self.evaluation = evaluation
        self.opportunity = opportunity; self.business = business; self.governor = governor
        self.experiment_submitter = experiment_submitter

    def set_experiment_submitter(self, submitter: Callable[[Any], str] | None) -> None:
        self.experiment_submitter = submitter

    def _authorize_cycle(self, objective: str) -> str:
        request = DecisionRequest(
            actor=Actor(id="enterprise-orchestrator", role="system-orchestrator", autonomy=AutonomyLevel.A2),
            action=ActionClass.BUILD,
            reason="run canonical enterprise cycle",
            payload={"objective": objective},
        )
        decision = self.governor.evaluate(request)
        if not decision.allowed:
            raise PermissionError(f"enterprise cycle denied by Governor: {decision.reason}")
        return request.id

    def _save_experiment_context(self, experiment_id: str, *, objective: str, approved: bool, economic_feedback: dict[str, Any]) -> None:
        self.store._write_state(f"experiment.context:{experiment_id}", {"objective": objective, "approved": approved, "economic_feedback": economic_feedback})

    def _load_experiment_context(self, experiment_id: str) -> dict[str, Any]:
        return self.store._read_state(f"experiment.context:{experiment_id}") or {}

    def _load_durable_experiment(self, experiment_id: str) -> Experiment | None:
        experiment = self.store.experiments.get(experiment_id)
        if experiment is not None:
            return experiment
        with self.runtime_store.lock:
            row = self.runtime_store.db.execute("SELECT experiment_id,hypothesis,success_criteria,status,result FROM experiments WHERE experiment_id=?", (experiment_id,)).fetchone()
        if row is None:
            return None
        experiment = Experiment(id=row[0], hypothesis=row[1], success_criteria=json.loads(row[2]), status=row[3], result=json.loads(row[4]) if row[4] else None)
        self.store.experiments[experiment.id] = experiment
        return experiment

    def run(self, objective: str, *, approved: bool = False, economic_feedback: dict[str, Any] | None = None) -> EnterpriseCycle:
        objective = objective.strip()
        if not objective: raise ValueError("enterprise objective is required")
        governor_request_id = self._authorize_cycle(objective)
        economic_feedback = economic_feedback or {}
        self.store.record("enterprise.cycle.started", objective=objective, economic_feedback=economic_feedback, governor_request_id=governor_request_id)
        research = self.research.run(objective, self.store)
        academy = self.academy.run(research, self.store)
        knowledge = self.knowledge_engine.run(academy, self.store)
        innovation = self.innovation.run(knowledge, self.store)
        experiment = self.experiment.run(innovation, self.store)
        if experiment.get("experiment_id") and self.experiment_submitter is not None:
            experiment_record = self.store.experiments.get(experiment["experiment_id"])
            if experiment_record is None: raise RuntimeError("experiment proposal was not persisted in the canonical engine store")
            self._save_experiment_context(experiment_record.id, objective=objective, approved=approved, economic_feedback=economic_feedback)
            job_id = self.experiment_submitter(experiment_record)
            experiment["execution_job_id"] = job_id; experiment["status"] = "queued"
            evaluation = {"experiment_id": experiment["experiment_id"], "passed": False, "reason": "awaiting_execution", "execution_job_id": job_id}
            opportunity = {"status": "awaiting_execution", "reason": "experiment must complete before opportunity qualification", "experiment_id": experiment["experiment_id"]}
            business = {"status": "awaiting_execution", "reason": "experiment must complete before business execution"}
            self.store.record("experiment.queued", experiment_id=experiment["experiment_id"], job_id=job_id)
        else:
            evaluation = self.evaluation.run(experiment, self.store)
            opportunity = self.opportunity.run(evaluation, self.store, economic_feedback=economic_feedback)
            business = self.business.run(opportunity, approved=approved)
        status = business.get("status") or opportunity.get("status") or evaluation.get("reason")
        self.store.record("enterprise.cycle.completed", objective=objective, status=status, governor_request_id=governor_request_id)
        return EnterpriseCycle(objective, research, academy, knowledge, innovation, experiment, evaluation, opportunity, business)

    def continue_after_experiment(self, experiment_id: str) -> dict[str, Any]:
        experiment = self._load_durable_experiment(experiment_id)
        if experiment is None: raise KeyError(f"experiment not found: {experiment_id}")
        if experiment.status != "complete" or experiment.result is None:
            return {"status": "awaiting_measurement", "experiment_id": experiment_id}
        context = self._load_experiment_context(experiment_id)
        if context.get("completed") and context.get("final_result"): return dict(context["final_result"])
        objective = str(context.get("objective", "")).strip()
        if not objective: raise RuntimeError("experiment continuation context is missing objective")
        governor_request_id = self._authorize_cycle(objective)
        approved = bool(context.get("approved", False)); economic_feedback = context.get("economic_feedback") or {}
        evaluation = self.evaluation.run({"experiment_id": experiment.id, "status": experiment.status, "criteria": experiment.success_criteria, "result": experiment.result}, self.store)
        opportunity = self.opportunity.run(evaluation, self.store, economic_feedback=economic_feedback)
        business = self.business.run(opportunity, approved=approved)
        status = business.get("status") or opportunity.get("status") or evaluation.get("reason", "completed")
        final_result = {"status": status, "experiment_id": experiment_id, "objective": objective, "evaluation": evaluation, "opportunity": opportunity, "business": business, "governor_request_id": governor_request_id}
        self.store.record("enterprise.cycle.resumed", objective=objective, experiment_id=experiment_id, status=status, governor_request_id=governor_request_id)
        self.store._write_state(f"experiment.context:{experiment_id}", {**context, "completed": True, "final_status": status, "final_result": final_result})
        return final_result
