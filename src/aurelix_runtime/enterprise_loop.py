"""Single connected enterprise loop for AURELIX.

Every specialist remains responsible for its own role, while this coordinator
makes their outputs flow into the next role and records the complete cycle in
one durable state boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .integrated_engines import EngineStore


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

    def __init__(self, *, runtime_store, knowledge_repository, research, academy,
                 knowledge_engine, innovation, experiment, evaluation, opportunity, business):
        self.store = EngineStore(runtime_store, knowledge_repository)
        self.research = research
        self.academy = academy
        self.knowledge_engine = knowledge_engine
        self.innovation = innovation
        self.experiment = experiment
        self.evaluation = evaluation
        self.opportunity = opportunity
        self.business = business

    def run(self, objective: str, *, approved: bool = False,
            economic_feedback: dict[str, Any] | None = None) -> EnterpriseCycle:
        objective = objective.strip()
        if not objective:
            raise ValueError("enterprise objective is required")
        self.store.record("enterprise.cycle.started", objective=objective,
                          economic_feedback=economic_feedback or {})

        research = self.research.run(objective, self.store)
        academy = self.academy.run(research, self.store)
        knowledge = self.knowledge_engine.run(academy, self.store)
        innovation = self.innovation.run(knowledge, self.store)
        experiment = self.experiment.run(innovation, self.store)
        evaluation = self.evaluation.run(experiment, self.store)
        opportunity = self.opportunity.run(evaluation, self.store,
                                           economic_feedback=economic_feedback or {})
        business = self.business.run(opportunity, approved=approved)

        status = business.get("status") or opportunity.get("status")
        self.store.record("enterprise.cycle.completed", objective=objective, status=status)
        return EnterpriseCycle(objective, research, academy, knowledge, innovation, experiment, evaluation, opportunity, business)
