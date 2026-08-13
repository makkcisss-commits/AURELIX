"""End-to-end orchestration for the governed research-to-business path."""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from aurelix_runtime.integrated_engines import EngineStore, Experiment


class IntelligenceFlow:
    """Coordinates the complete intelligence lifecycle without inventing results."""

    def __init__(self, factory):
        self.factory = factory

    def research_to_experiment(self, query: str) -> dict[str, Any]:
        """Prepare the research-to-experiment path without claiming execution."""
        research = self.factory.research_and_store(query)
        store = EngineStore()
        academy = self.factory.academy.run({"objective": query, "evidence": list(research.evidence)}, store)
        knowledge = self.factory.knowledge_engine.run(academy, store)
        innovation = self.factory.innovation.run(knowledge, store)
        experiment = Experiment(str(uuid4()), innovation.get("proposed_solution", innovation.get("title", "unknown")), [{"metric": "success", "operator": ">=", "target": 1.0}])
        store.experiments[experiment.id] = experiment
        store.record("experiment.proposed", experiment_id=experiment.id)
        experiment_payload = {"experiment_id": experiment.id, "status": experiment.status, "criteria": experiment.success_criteria, "result": None}
        evaluation = self.factory.evaluation.run(experiment_payload, store)
        opportunity = self.factory.opportunity.run(evaluation, store)
        business = self.factory.business.run(opportunity, approved=False)
        self.factory.runtime.register_experiment(experiment)
        return {"query": query, "evidence_count": len(research.evidence), "knowledge_ids": list(research.knowledge_ids), "academy": academy, "innovation": innovation, "experiment": experiment_payload, "evaluation": evaluation, "opportunity": opportunity, "business": business}

    def execute_experiment(self, experiment_id: str, observations: list[dict[str, Any]]) -> dict[str, Any]:
        experiments = self.factory.runtime.query_experiments()
        match = next((item for item in experiments if item.get("experiment_id") == experiment_id), None)
        if match is None:
            raise KeyError(f"experiment not found: {experiment_id}")
        for observation in observations:
            self.factory.runtime.record_observation(experiment_id, observation)
        experiment = self.factory.runtime.get_experiment(experiment_id)
        run = self.factory.experiment_runner.execute(experiment)
        return {"experiment_id": experiment_id, "status": run.status, "evaluation": {"passed": run.evaluation.passed, "confidence": run.evaluation.confidence, "reasons": list(run.evaluation.reasons)} if run.evaluation else None}
