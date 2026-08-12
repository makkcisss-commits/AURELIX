"""Composition root for AURELIX engines and external providers."""
from __future__ import annotations

import os
from dataclasses import dataclass

from .model_gateway import GovernedModelGateway, ModelProvider
from .research import ResearchEngine
from ..aurelix_runtime.integrated_engines import AcademyEngine, InnovationEngine, KnowledgeEngine, ExperimentEngine, EvaluationEngine, OpportunityEngine, BusinessEngine
from ..aurelix_runtime.knowledge_store import InMemoryKnowledgeRepository, KnowledgeRepository
from ..aurelix_runtime.research_knowledge import ResearchToKnowledge
from ..aurelix_runtime.research_provider import HttpResearchProvider, TavilyResearchProvider


@dataclass
class EngineFactory:
    """Single composition root; no engine chooses a provider by itself."""
    model_gateway: GovernedModelGateway | None
    research_provider: object | None
    knowledge: KnowledgeRepository
    research_to_knowledge: ResearchToKnowledge | None
    academy: AcademyEngine
    knowledge_engine: KnowledgeEngine
    innovation: InnovationEngine
    experiment: ExperimentEngine
    evaluation: EvaluationEngine
    opportunity: OpportunityEngine
    business: BusinessEngine

    @classmethod
    def from_env(cls, *, model_provider: ModelProvider | None = None, policy=None, audit=None, knowledge: KnowledgeRepository | None = None):
        if model_provider is None:
            from .model_gateway import OpenAICompatibleProvider
            model_provider = OpenAICompatibleProvider.from_env()
        gateway = GovernedModelGateway(model_provider, policy=policy, audit=audit) if model_provider else None
        provider = HttpResearchProvider.from_env()
        repository = knowledge or InMemoryKnowledgeRepository()
        bridge = ResearchToKnowledge(provider, repository) if provider else None
        return cls(
            model_gateway=gateway,
            research_provider=provider,
            knowledge=repository,
            research_to_knowledge=bridge,
            academy=AcademyEngine(),
            knowledge_engine=KnowledgeEngine(),
            innovation=InnovationEngine(),
            experiment=ExperimentEngine(),
            evaluation=EvaluationEngine(),
            opportunity=OpportunityEngine(),
            business=BusinessEngine(),
        )

    def research_and_store(self, query: str):
        if self.research_to_knowledge is None:
            raise RuntimeError("no research provider configured")
        return self.research_to_knowledge.research_and_store(query)
