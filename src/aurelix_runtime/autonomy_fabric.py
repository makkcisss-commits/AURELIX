"""Single durable orchestration boundary for AURELIX autonomy."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from .integrated_engines import (
    AcademyEngine, BusinessEngine, EngineStore, EvaluationEngine,
    ExperimentEngine, InnovationEngine, KnowledgeEngine, OpportunityEngine,
    ResearchEngine,
)
from .persistence import RuntimeStore


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
    """Run the complete research-to-business chain under one execution."""

    def __init__(self, store: RuntimeStore | None = None, engine_store: EngineStore | None = None,
                 research: ResearchEngine | None = None, academy: AcademyEngine | None = None,
                 knowledge: KnowledgeEngine | None = None, innovation: InnovationEngine | None = None,
                 experiment: ExperimentEngine | None = None, evaluation: EvaluationEngine | None = None,
                 opportunity: OpportunityEngine | None = None, business: BusinessEngine | None = None) -> None:
        self.store = store or RuntimeStore()
        self.engines = engine_store or EngineStore(runtime_store=self.store)
        self.research = research or ResearchEngine()
        self.academy = academy or AcademyEngine()
        self.knowledge = knowledge or KnowledgeEngine()
        self.innovation = innovation or InnovationEngine()
        self.experiment = experiment or ExperimentEngine()
        self.evaluation = evaluation or EvaluationEngine()
        self.opportunity = opportunity or OpportunityEngine()
        self.business = business or BusinessEngine(require_approval=True)

    def run(self, objective: str, execution_id: str | None = None) -> AutonomyRun:
        execution_id = execution_id or str(uuid4())
        job = self.store.enqueue("autonomy.run", {"objective": objective}, execution_id=execution_id)
        worker_id = f"autonomy:{execution_id}"
        claimed = self.store.claim(job.job_id, worker_id=worker_id)
        if claimed is None:
            raise RuntimeError(f"autonomy execution is not claimable: {execution_id}")
        self.store.record_audit(execution_id, "autonomy.started", {"objective": objective, "actor": worker_id})
        try:
            research = self.research.run(objective, self.engines)
            self.store.record_audit(execution_id, "autonomy.research", {"evidence_count": len(research.get("evidence", []))})
            academy = self.academy.run(research, self.engines)
            knowledge = self.knowledge.run(academy, self.engines)
            innovation = self.innovation.run(knowledge, self.engines)
            experiment = self.experiment.run(innovation, self.engines)
            evaluation = self.evaluation.run(experiment, self.engines)
            opportunity = self.opportunity.run(evaluation, self.engines)
            business = self.business.run(opportunity, approved=False)
            result = {
                "execution_id": execution_id,
                "status": "awaiting_approval" if business.get("status") == "awaiting_approval" else "completed",
                "research": research, "academy": academy, "knowledge": knowledge,
                "innovation": innovation, "experiment": experiment, "evaluation": evaluation,
                "opportunity": opportunity, "business": business,
            }
            self.store.complete(execution_id, result, worker_id=worker_id, lease_token=claimed.lease_token)
            self.store.record_audit(execution_id, "autonomy.completed", {"status": result["status"], "worker_id": worker_id})
            return AutonomyRun(**result)
        except Exception as exc:
            self.store.finish(execution_id, False, str(exc), retry=False, worker_id=worker_id, lease_token=claimed.lease_token)
            self.store.record_audit(execution_id, "autonomy.failed", {"error": type(exc).__name__})
            raise

    def close(self) -> None:
        self.store.close()
