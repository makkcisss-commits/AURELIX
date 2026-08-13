"""Composition root for AURELIX engines and external providers."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from .development_providers import DevelopmentModelProvider, development_research_provider
from .evaluation import EvaluationEngine as CoreEvaluationEngine
from .model_gateway import GenerationRequest, GovernedModelGateway, ModelProvider, OpenAICompatibleProvider
from .models import ActionClass, Actor, AutonomyLevel, DecisionRequest
from .policy import PolicyEngine
from aurelix_runtime.enterprise_loop import EnterpriseLoop
from aurelix_runtime.integrated_engines import (
    AcademyEngine, BusinessEngine, EvaluationEngine, ExperimentEngine,
    InnovationEngine, KnowledgeEngine, OpportunityEngine, ResearchEngine,
)
from aurelix_runtime.knowledge_store import KnowledgeRepository, SQLiteKnowledgeRepository
from aurelix_runtime.research_knowledge import ResearchToKnowledge
from aurelix_runtime.research_provider import HttpResearchProvider, TavilyResearchProvider
from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig
from aurelix_runtime.system_diagnostics import SystemDiagnostics
from aurelix_runtime.system_developer import SystemDeveloper


@dataclass(frozen=True)
class EngineFactoryConfig:
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    register_autonomy: bool = True


class EngineFactory:
    """Canonical engine composition root sharing one durable runtime and knowledge store."""

    def __init__(self, config: EngineFactoryConfig | None = None, runtime: AurelixRuntime | None = None,
                 model_provider: ModelProvider | None = None, research_provider=None,
                 knowledge: KnowledgeRepository | None = None):
        self.config = config or EngineFactoryConfig()
        self.runtime = runtime or AurelixRuntime(self.config.runtime)
        if self.config.register_autonomy:
            self.runtime.register_autonomy()
        self.policy_engine = PolicyEngine()
        development_mode = os.getenv("AURELIX_MODE", "production").strip().lower() == "development"
        self.model_provider = model_provider if model_provider is not None else (
            DevelopmentModelProvider() if development_mode else OpenAICompatibleProvider.from_env()
        )
        self.model_gateway = self._build_model_gateway(self.model_provider)
        self.research_provider = research_provider if research_provider is not None else (
            development_research_provider if development_mode else self._build_research_provider()
        )
        self.knowledge: KnowledgeRepository = knowledge or SQLiteKnowledgeRepository(self.runtime.store)
        self.research = ResearchEngine(self.research_provider)
        self.research_to_knowledge = ResearchToKnowledge(self.research_provider, self.knowledge) if self.research_provider else None
        self.academy = AcademyEngine(self.model_gateway)
        self.knowledge_engine = KnowledgeEngine()
        self.innovation = InnovationEngine(self.model_gateway)
        self.experiment = ExperimentEngine()
        self.evaluation = EvaluationEngine()
        self.opportunity = OpportunityEngine()
        self.business = BusinessEngine(require_approval=True)
        self.enterprise = EnterpriseLoop(
            runtime_store=self.runtime.store,
            knowledge_repository=self.knowledge,
            research=self.research,
            academy=self.academy,
            knowledge_engine=self.knowledge_engine,
            innovation=self.innovation,
            experiment=self.experiment,
            evaluation=self.evaluation,
            opportunity=self.opportunity,
            business=self.business,
        )
        self.experiment_runner = self.runtime.create_experiment_runner()
        self.core_evaluation = CoreEvaluationEngine()
        self.diagnostics = SystemDiagnostics(self)
        self.system_developer = SystemDeveloper(self.diagnostics)

    def _build_model_gateway(self, provider: ModelProvider | None) -> GovernedModelGateway | None:
        if provider is None:
            return None

        def policy(request: GenerationRequest) -> bool:
            decision = self.policy_engine.evaluate(DecisionRequest(
                actor=Actor(request.actor_id, "engine", AutonomyLevel.A1),
                action=ActionClass.RESEARCH, reason=request.action,
                payload={"prompt": request.prompt},
            ))
            return decision.allowed

        def audit(event: str, **metadata: Any) -> None:
            outcome = "failed" if event.endswith(".failed") else "denied" if event.endswith(".denied") else "requested" if event.endswith(".requested") else "succeeded" if event.endswith(".completed") else "recorded"
            self.runtime.store.audit(event, str(metadata.get("actor_id", "system")), str(metadata.get("action", "model")), outcome, metadata)

        return GovernedModelGateway(provider, policy=policy, audit=audit)

    @staticmethod
    def _build_research_provider():
        provider = os.getenv("AURELIX_RESEARCH_PROVIDER", "http").strip().lower()
        if provider == "tavily":
            return TavilyResearchProvider.from_env()
        return HttpResearchProvider.from_env()

    def research_and_store(self, query: str):
        if self.research_to_knowledge is None:
            raise RuntimeError("no research provider configured")
        return self.research_to_knowledge.research_and_store(query)

    def run_enterprise_cycle(self, objective: str, *, approved: bool = False):
        """Run the complete connected specialist chain through one durable boundary."""
        return self.enterprise.run(objective, approved=approved)

    def diagnose(self):
        """Return a live, actionable system health report."""
        return self.diagnostics.run()

    def plan_system_change(self, objective: str, scope: list[str] | None = None):
        return self.system_developer.plan(objective, scope)

    def generate(self, prompt: str, *, action: str = "engine.generate", actor_id: str = "engine") -> str:
        if self.model_gateway is None:
            raise RuntimeError("AURELIX_MODEL_BASE_URL is not configured")
        return self.model_gateway.generate(GenerationRequest(prompt=prompt, action=action, actor_id=actor_id))
