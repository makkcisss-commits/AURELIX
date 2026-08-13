"""End-to-end governed pipeline for Research through Business."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
from uuid import uuid4

from .governance import GovernanceGate, Transition
from .integrated_engines import (
    AcademyEngine, BusinessEngine, EngineStore, EvaluationEngine,
    ExperimentEngine, InnovationEngine, KnowledgeEngine, OpportunityEngine,
    ResearchEngine,
)
from .research_provider import HttpResearchProvider


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
    """Runs the complete intelligence lifecycle with mandatory provenance gates."""

    def __init__(self, store: Optional[EngineStore] = None, research_engine: Optional[ResearchEngine] = None,
                 governance: Optional[GovernanceGate] = None):
        self.store = store or EngineStore()
        self.governance = governance or GovernanceGate()
        self.research = research_engine or ResearchEngine(provider=HttpResearchProvider.from_env())
        self.academy = AcademyEngine()
        self.knowledge = KnowledgeEngine()
        self.innovation = InnovationEngine()
        self.experiment = ExperimentEngine()
        self.evaluation = EvaluationEngine()
        self.opportunity = OpportunityEngine()
        self.business = BusinessEngine(require_approval=True)

    def _transition(self, object_type: str, parent_id: str | None = None) -> str:
        object_id = f"{object_type}-{uuid4()}"
        parents = () if parent_id is None else (parent_id,)
        self.governance.register(Transition(object_id, object_type, parents, "aurelix-pipeline", "advance"))
        self.store.record("governance.transition", object_id=object_id, object_type=object_type, parent_id=parent_id or "")
        return object_id

    def run(self, objective: str, business_approved: bool = False) -> PipelineResult:
        research = self.research.run(objective, self.store)
        research_id = self._transition("research")
        academy = self.academy.run(research, self.store)
        academy_id = self._transition("academy", research_id)
        knowledge = self.knowledge.run(academy, self.store)
        knowledge_id = self._transition("knowledge", academy_id)
        innovation = self.innovation.run(knowledge, self.store)
        innovation_id = self._transition("innovation", knowledge_id)
        experiment = self.experiment.run(innovation, self.store)
        experiment_id = self._transition("experiment", innovation_id)
        evaluation = self.evaluation.run(experiment, self.store)
        evaluation_id = self._transition("evaluation", experiment_id)
        opportunity = self.opportunity.run(evaluation, self.store)
        opportunity_id = self._transition("opportunity", evaluation_id)
        business = self.business.run(opportunity, approved=business_approved)
        self._transition("business", opportunity_id)
        self.store.record("pipeline.completed", objective=objective, business_status=business["status"])
        return PipelineResult(research, academy, knowledge, innovation, experiment, evaluation, opportunity, business)
