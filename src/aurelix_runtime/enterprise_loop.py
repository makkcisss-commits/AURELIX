"""Single connected enterprise loop for AURELIX.

Every specialist remains responsible for its own role, while this coordinator
makes their outputs flow into the next role and records the complete cycle in
one durable state boundary.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

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
    """The orchestration boundary: no specialist is an isolated island."""

    def __init__(self, *, runtime_store, knowledge_repository, research, academy, knowledge_engine, innovation, experiment, evaluation, opportunity, business,
                 experiment_submitter: Callable[[Any], str] | None = None):
        self.runtime_store = runtime_store
        self.store = EngineStore(runtime_store, knowledge_repository)
        self.research = research
        self.academy = academy
        self.knowledge_engine = knowledge_engine
        self.innovation = innovation
        self.experiment = experiment
        self.evaluation = evaluation
        self.opportunity = opportunity
        self.business = business
        self.experiment_submitter = experiment_submitter

    def set_experiment_submitter(self, submitter: Callable[[Any], str] | None) -> None:
        self.experiment_submitter = submitter

    def _save_experiment_context(self, experiment_id: str, *, objective: str, approved: bool, economic_feedback: dict[str, Any]) -> None:
        self.store._write_state(
            f"experiment.context:{experiment_id}",
            {"objective": objective, "approved": approved, "economic_feedback": economic_feedback},
        )

    def _load_experiment_context(self, experiment_id: str) -> dict[str, Any]:
        return self.store._read_state(f"experiment.context:{experiment_id}") or {}

    def _claim_experiment_continuation(self, experiment_id: str, context: dict[str, Any], *, lease_seconds: float = 60.0) -> tuple[bool, dict[str, Any]]:
        """Atomically claim downstream continuation so concurrent workers cannot duplicate business effects.

        A short durable lease makes the claim recoverable if the worker dies before it
        records the final result. A completed context always wins over an active claim.
        """
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        lease_until = (now + timedelta(seconds=max(1.0, lease_seconds))).isoformat()
        token = str(uuid.uuid4())
        key = f"experiment.context:{experiment_id}"
        with self.runtime_store.lock:
            self.runtime_store.db.execute("BEGIN IMMEDIATE")
            try:
                row = self.runtime_store.db.execute("SELECT value FROM runtime_state WHERE key=?", (key,)).fetchone()
                current = json.loads(row[0]) if row else dict(context)
                if current.get("completed") and current.get("final_result"):
                    self.runtime_store.db.commit()
                    return False, current
                active_until = current.get("continuation_lease_until")
                active = False
                if active_until:
                    try:
                        active = datetime.fromisoformat(active_until) > now
                    except ValueError:
                        active = False
                if active:
                    self.runtime_store.db.commit()
                    return False, current
                claimed = {
                    **current,
                    "continuation_token": token,
                    "continuation_lease_until": lease_until,
                }
                self.runtime_store.db.execute(
                    "INSERT INTO runtime_state(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (key, json.dumps(claimed, sort_keys=True)),
                )
                self.runtime_store.db.commit()
                return True, claimed
            except Exception:
                self.runtime_store.db.rollback()
                raise

    def _complete_experiment_continuation(self, experiment_id: str, context: dict[str, Any], token: str, final_result: dict[str, Any]) -> None:
        key = f"experiment.context:{experiment_id}"
        with self.runtime_store.lock:
            self.runtime_store.db.execute("BEGIN IMMEDIATE")
            try:
                row = self.runtime_store.db.execute("SELECT value FROM runtime_state WHERE key=?", (key,)).fetchone()
                current = json.loads(row[0]) if row else {}
                if current.get("completed") and current.get("final_result"):
                    self.runtime_store.db.commit()
                    return
                if current.get("continuation_token") != token:
                    self.runtime_store.db.rollback()
                    raise RuntimeError(f"experiment continuation lease lost: {experiment_id}")
                completed = {
                    **context,
                    "completed": True,
                    "final_status": final_result.get("status"),
                    "final_result": final_result,
                    "continuation_token": None,
                    "continuation_lease_until": None,
                }
                self.runtime_store.db.execute(
                    "INSERT INTO runtime_state(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (key, json.dumps(completed, sort_keys=True)),
                )
                self.runtime_store.db.commit()
            except Exception:
                self.runtime_store.db.rollback()
                raise

    def _load_durable_experiment(self, experiment_id: str) -> Experiment | None:
        """Reconcile the in-memory EngineStore with the Runtime SQL boundary."""
        experiment = self.store.experiments.get(experiment_id)
        if experiment is not None:
            return experiment
        with self.runtime_store.lock:
            row = self.runtime_store.db.execute(
                "SELECT experiment_id,hypothesis,success_criteria,status,result FROM experiments WHERE experiment_id=?",
                (experiment_id,),
            ).fetchone()
        if row is None:
            return None
        experiment = Experiment(
            id=row[0], hypothesis=row[1], success_criteria=json.loads(row[2]),
            status=row[3], result=json.loads(row[4]) if row[4] else None,
        )
        self.store.experiments[experiment.id] = experiment
        return experiment

    def run(self, objective: str, *, approved: bool = False, economic_feedback: dict[str, Any] | None = None) -> EnterpriseCycle:
        objective = objective.strip()
        if not objective:
            raise ValueError("enterprise objective is required")
        economic_feedback = economic_feedback or {}
        self.store.record("enterprise.cycle.started", objective=objective, economic_feedback=economic_feedback)
        research = self.research.run(objective, self.store)
        academy = self.academy.run(research, self.store)
        knowledge = self.knowledge_engine.run(academy, self.store)
        innovation = self.innovation.run(knowledge, self.store)
        experiment = self.experiment.run(innovation, self.store)
        if experiment.get("experiment_id") and self.experiment_submitter is not None:
            experiment_record = self.store.experiments.get(experiment["experiment_id"])
            if experiment_record is None:
                raise RuntimeError("experiment proposal was not persisted in the canonical engine store")
            self._save_experiment_context(experiment_record.id, objective=objective, approved=approved, economic_feedback=economic_feedback)
            job_id = self.experiment_submitter(experiment_record)
            experiment["execution_job_id"] = job_id
            experiment["status"] = "queued"
            evaluation = {"experiment_id": experiment["experiment_id"], "passed": False, "reason": "awaiting_execution", "execution_job_id": job_id}
            opportunity = {"status": "awaiting_execution", "reason": "experiment must complete before opportunity qualification", "experiment_id": experiment["experiment_id"]}
            business = {"status": "awaiting_execution", "reason": "experiment must complete before business execution"}
            self.store.record("experiment.queued", experiment_id=experiment["experiment_id"], job_id=job_id)
        else:
            evaluation = self.evaluation.run(experiment, self.store)
            opportunity = self.opportunity.run(evaluation, self.store, economic_feedback=economic_feedback)
            business = self.business.run(opportunity, approved=approved)
        status = business.get("status") or opportunity.get("status") or evaluation.get("reason")
        self.store.record("enterprise.cycle.completed", objective=objective, status=status)
        return EnterpriseCycle(objective, research, academy, knowledge, innovation, experiment, evaluation, opportunity, business)

    def continue_after_experiment(self, experiment_id: str) -> dict[str, Any]:
        """Resume a durable enterprise cycle after real experiment completion exactly once at the effect boundary."""
        experiment = self._load_durable_experiment(experiment_id)
        if experiment is None:
            raise KeyError(f"experiment not found: {experiment_id}")
        if experiment.status != "complete" or experiment.result is None:
            return {"status": "awaiting_measurement", "experiment_id": experiment_id}
        context = self._load_experiment_context(experiment_id)
        if context.get("completed") and context.get("final_result"):
            return dict(context["final_result"])
        claimed, context = self._claim_experiment_continuation(experiment_id, context)
        if not claimed:
            if context.get("completed") and context.get("final_result"):
                return dict(context["final_result"])
            return {"status": "continuation_in_progress", "experiment_id": experiment_id}
        token = str(context["continuation_token"])
        objective = str(context.get("objective", "")).strip()
        if not objective:
            raise RuntimeError("experiment continuation context is missing objective")
        approved = bool(context.get("approved", False))
        economic_feedback = context.get("economic_feedback") or {}
        evaluation = self.evaluation.run(
            {"experiment_id": experiment.id, "status": experiment.status, "criteria": experiment.success_criteria, "result": experiment.result},
            self.store,
        )
        opportunity = self.opportunity.run(evaluation, self.store, economic_feedback=economic_feedback)
        business = self.business.run(opportunity, approved=approved)
        status = business.get("status") or opportunity.get("status") or evaluation.get("reason", "completed")
        final_result = {
            "status": status,
            "experiment_id": experiment_id,
            "objective": objective,
            "evaluation": evaluation,
            "opportunity": opportunity,
            "business": business,
        }
        self.store.record("enterprise.cycle.resumed", objective=objective, experiment_id=experiment_id, status=status)
        self._complete_experiment_continuation(experiment_id, context, token, final_result)
        return final_result
