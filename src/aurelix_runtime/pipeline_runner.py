"""End-to-end governed pipeline for Research through Business."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .integrated_engines import (
    AcademyEngine, BusinessEngine, EngineStore, EvaluationEngine,
    ExperimentEngine, InnovationEngine, KnowledgeEngine, OpportunityEngine,
    ResearchEngine,
)


@dataclass
class PipelineResult:
    research: Dict[str, Any]
    academy: Dict[str, Any]
    knowledge: Dict[str, Any]
    innovation: Dict[str, Any]
    experiment: Dict[str, Any]
    evaluation: Dict[str, Any]
    opportunity: Dict[str, Any]
    business: Dict[str, Any]


class GovernedPipeline:
    """Runs the complete intelligence lifecycle with Business approval-gated."""

    def __init__(self, store: Optional[EngineStore] = None, research_engine: Optional[ResearchEngine] = None):
        self.store = store or EngineStore()
        self.research = research_engine or ResearchEngine()
        self.academy = AcademyEngine()
        self.knowledge = KnowledgeEngine()
        self.innovation = InnovationEngine()
        self.experiment = ExperimentEngine()
        self.evaluation = EvaluationEngine()
        self.opportunity = OpportunityEngine()
        self.business = BusinessEngine(require_approval=True)

    def run(self, objective: str, business_approved: bool = False) -> PipelineResult:
        research = self.research.run(objective, self.store)
        academy = self.academy.run(research, self.store)
        knowledge = self.knowledge.run(academy, self.store)
        innovation = self.innovation.run(knowledge, self.store)
        experiment = self.experiment.run(innovation, self.store)
        evaluation = self.evaluation.run(experiment, self.store)
        opportunity = self.opportunity.run(evaluation, self.store)
        business = self.business.run(opportunity, approved=business_approved)
        self.store.record("pipeline.completed", objective=objective, business_status=business["status"])
        return PipelineResult(research, academy, knowledge, innovation, experiment, evaluation, opportunity, business)
