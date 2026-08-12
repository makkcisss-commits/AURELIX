"""Composition root for AURELIX engines and external providers."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from .evaluation import EvaluationEngine as CoreEvaluationEngine
from .model_gateway import GenerationRequest, GovernedModelGateway, ModelProvider, OpenAICompatibleProvider
from .models import ActionClass, Actor, AutonomyLevel, DecisionRequest
from .policy import PolicyEngine
from aurelix_runtime.integrated_engines import (
    AcademyEngine,
    BusinessEngine,
    EvaluationEngine,
    ExperimentEngine,
    InnovationEngine,
    KnowledgeEngine,
    OpportunityEngine,
    ResearchEngine,
)
from aurelix_runtime.knowledge_store import InMemoryKnowledgeRepository, KnowledgeRepository
from aurelix_runtime.postgres_knowledge_repository import PostgresKnowledgeRepository
from aurelix_runtime.research_knowledge import ResearchToKnowledge
from aurelix_runtime.research_provider import HttpResearchProvider, TavilyResearchProvider
from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig


@dataclass(frozen=True)
class EngineFactoryConfig:
    runtime: RuntimeConfig = RuntimeConfig()


class EngineFactory:
    """Single composition root; no engine chooses infrastructure by itself."""

    def __init__(
        self,
        config: EngineFactoryConfig | None = None,
        runtime: AurelixRuntime | None = None,
        model_provider: ModelProvider | None = None,
        research_provider=None,
        knowledge: KnowledgeRepository | None = None,
    ):
        self.config = config or EngineFactoryConfig()
        self.runtime = runtime or AurelixRuntime(self.config.runtime)
        self.policy_engine = PolicyEngine()
        self.model_provider = model_provider if model_provider is not None else OpenAICompatibleProvider.from_env()
        self.model_gateway = self._build_model_gateway(self.model_provider)
        self.research_provider = research_provider if research_provider is not None else self._build_research_provider()
        self.knowledge: KnowledgeRepository = knowledge or self._build_knowledge_repository()
        self.research = ResearchEngine(self.research_provider)
        self.research_to_knowledge = ResearchToKnowledge(self.research_provider, self.knowledge) if self.research_provider else None
        self.academy = AcademyEngine(self.model_gateway)
        self.knowledge_engine = KnowledgeEngine()
        self.innovation = InnovationEngine(self.model_gateway)
        self.experiment = ExperimentEngine()
        self.evaluation = EvaluationEngine()
        self.opportunity = OpportunityEngine()
        self.business = BusinessEngine()
        self.experiment_runner = self.runtime.create_experiment_runner()
        self.core_evaluation = CoreEvaluationEngine()

    def _build_model_gateway(self, provider: ModelProvider | None) -> GovernedModelGateway | None:
        if provider is None:
            return None

        def policy(request: GenerationRequest) -> bool:
            decision = self.policy_engine.evaluate(
                DecisionRequest(
                    actor=Actor(request.actor_id, "engine", AutonomyLevel.A1),
                    action=ActionClass.RESEARCH,
                    reason=request.action,
                    payload={"prompt": request.prompt},
                )
            )
            return decision.allowed

        def audit(event: str, **metadata: Any) -> None:
            if event.endswith(".failed"):
                outcome = "failed"
            elif event.endswith(".denied"):
                outcome = "denied"
            elif event.endswith(".requested"):
                outcome = "requested"
            elif event.endswith(".completed"):
                outcome = "succeeded"
            else:
                outcome = "recorded"
            self.runtime.store.audit(
                event,
                str(metadata.get("actor_id", "system")),
                str(metadata.get("action", "model")),
                outcome,
                metadata,
            )

        return GovernedModelGateway(provider, policy=policy, audit=audit)

    @staticmethod
    def _build_research_provider():
        provider = os.getenv("AURELIX_RESEARCH_PROVIDER", "http").strip().lower()
        if provider == "tavily":
            return TavilyResearchProvider.from_env()
        return HttpResearchProvider.from_env()

    @staticmethod
    def _build_knowledge_repository() -> KnowledgeRepository:
        url = os.getenv("AURELIX_DATABASE_URL", "").strip()
        if url:
            return PostgresKnowledgeRepository(url)
        return InMemoryKnowledgeRepository()

    def research_and_store(self, query: str):
        if self.research_to_knowledge is None:
            raise RuntimeError("no research provider configured")
        return self.research_to_knowledge.research_and_store(query)

    def generate(self, prompt: str, *, action: str = "engine.generate", actor_id: str = "engine") -> str:
        if self.model_gateway is None:
            raise RuntimeError("AURELIX_MODEL_BASE_URL is not configured")
        return self.model_gateway.generate(GenerationRequest(prompt=prompt, action=action, actor_id=actor_id))
