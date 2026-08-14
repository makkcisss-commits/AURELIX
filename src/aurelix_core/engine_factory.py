"""Composition root for AURELIX engines and external providers."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from .development_providers import DevelopmentModelProvider, development_research_provider
from .evaluation import EvaluationEngine as CoreEvaluationEngine
from .economic_feedback import EconomicFeedback
from .governor import Governor
from .audit import AuditLog
from .continuous_intelligence import ContinuousIntelligence
from .capability_escalation import CapabilityEscalator
from .model_gateway import GenerationRequest, GovernedModelGateway, ModelProvider, OpenAICompatibleProvider
from .models import ActionClass, Actor, AutonomyLevel, DecisionRequest
from .policy import PolicyEngine
from .revenue_portfolio import RevenuePortfolio
from .system_orchestrator import SystemOrchestrator
from aurelix_runtime.autonomy_fabric import AutonomyFabric
from aurelix_runtime.enterprise_loop import EnterpriseLoop
from aurelix_runtime.integrated_engines import AcademyEngine, BusinessEngine, EvaluationEngine, ExperimentEngine, InnovationEngine, KnowledgeEngine, OpportunityEngine, ResearchEngine
from aurelix_runtime.knowledge_store import KnowledgeRepository, SQLiteKnowledgeRepository
from aurelix_runtime.knowledge_learning import KnowledgeLearningService
from aurelix_runtime.research_knowledge import ResearchToKnowledge
from aurelix_runtime.research_provider import HttpResearchProvider, TavilyResearchProvider
from aurelix_runtime.message_fabric import MessageFabric
from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig
from aurelix_runtime.self_improvement import SelfImprovementController
from aurelix_runtime.system_diagnostics import SystemDiagnostics
from aurelix_runtime.system_developer import SystemDeveloper
from aurelix_runtime.system_validation import SystemValidation

@dataclass(frozen=True)
class EngineFactoryConfig:
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    register_autonomy: bool = True

class EngineFactory:
    """Canonical engine composition root sharing one durable runtime and learning authority."""
    def __init__(self, config=None, runtime=None, model_provider=None, research_provider=None, knowledge=None, repository=None):
        self.config = config or EngineFactoryConfig()
        self.runtime = runtime or AurelixRuntime(self.config.runtime)
        self.policy_engine = PolicyEngine()
        self.audit = AuditLog()
        self.governor = Governor(policy=self.policy_engine, audit=self.audit)
        self.intelligence = ContinuousIntelligence()
        self.capability_escalator = CapabilityEscalator(self.intelligence)
        development_mode = os.getenv("AURELIX_MODE", "production").strip().lower() == "development"
        self.model_provider = model_provider if model_provider is not None else (DevelopmentModelProvider() if development_mode else OpenAICompatibleProvider.from_env())
        self.model_gateway = self._build_model_gateway(self.model_provider)
        self.research_provider = research_provider if research_provider is not None else (development_research_provider if development_mode else self._build_research_provider())
        self.knowledge = knowledge or SQLiteKnowledgeRepository(self.runtime.store)
        self.knowledge_learning = KnowledgeLearningService(self.knowledge)
        self.research = ResearchEngine(self.research_provider)
        self.research_to_knowledge = ResearchToKnowledge(self.research_provider, self.knowledge) if self.research_provider else None
        self.academy = AcademyEngine(self.model_gateway)
        self.knowledge_engine = KnowledgeEngine()
        self.innovation = InnovationEngine(self.model_gateway)
        self.experiment = ExperimentEngine()
        self.evaluation = EvaluationEngine()
        self.opportunity = OpportunityEngine()
        self.business = BusinessEngine(require_approval=True)
        self.revenue_portfolio = RevenuePortfolio()
        self.economic_feedback = EconomicFeedback(self.revenue_portfolio)
        self.enterprise = EnterpriseLoop(runtime_store=self.runtime.store, knowledge_repository=self.knowledge, research=self.research, academy=self.academy, knowledge_engine=self.knowledge_engine, innovation=self.innovation, experiment=self.experiment, evaluation=self.evaluation, opportunity=self.opportunity, business=self.business)
        self.message_fabric = MessageFabric()
        self.autonomy_fabric = None
        if self.config.register_autonomy:
            self.autonomy_fabric = AutonomyFabric(store=self.runtime.store, engine_store=self.enterprise.store, research=self.research, academy=self.academy, knowledge=self.knowledge_engine, innovation=self.innovation, experiment=self.experiment, evaluation=self.evaluation, opportunity=self.opportunity, business=self.business, message_fabric=self.message_fabric, capability_escalator=self.capability_escalator)
            self.runtime.register_claimed("autonomy.run", self.autonomy_fabric.run_claimed)
        self.experiment_runner = self.runtime.create_experiment_runner()
        self.core_evaluation = CoreEvaluationEngine()
        self.diagnostics = SystemDiagnostics(self)
        self.system_developer = SystemDeveloper(self.diagnostics, repository=repository)
        self.system_validation = SystemValidation(self)
        self.self_improvement = SelfImprovementController(self.diagnostics, self.system_developer)
        self.system_orchestrator = SystemOrchestrator(self, intelligence=self.intelligence, capability_escalator=self.capability_escalator)

    def _build_model_gateway(self, provider):
        if provider is None: return None
        def policy(request):
            decision = self.policy_engine.evaluate(DecisionRequest(actor=Actor(request.actor_id, "engine", AutonomyLevel.A1), action=ActionClass.RESEARCH, reason=request.action, payload={"prompt": request.prompt}))
            return decision.allowed
        def audit(event, **metadata):
            outcome = "failed" if event.endswith(".failed") else "denied" if event.endswith(".denied") else "requested" if event.endswith(".requested") else "succeeded" if event.endswith(".completed") else "recorded"
            self.runtime.store.audit(event, str(metadata.get("actor_id", "system")), str(metadata.get("action", "model")), outcome, metadata)
        return GovernedModelGateway(provider, policy=policy, audit=audit)

    @staticmethod
    def _build_research_provider():
        return TavilyResearchProvider.from_env() if os.getenv("AURELIX_RESEARCH_PROVIDER", "http").strip().lower() == "tavily" else HttpResearchProvider.from_env()

    def research_and_store(self, query):
        if self.research_to_knowledge is None: raise RuntimeError("no research provider configured")
        return self.research_to_knowledge.research_and_store(query)
    def run_enterprise_cycle(self, objective, *, approved=False): return self.enterprise.run(objective, approved=approved, economic_feedback=self.economic_learning_context())
    def run_system_cycle(self, objective): return self.system_orchestrator.run_cycle(objective)
    def record_verified_economic_outcome(self, **kwargs): return self.system_orchestrator.record_verified_economic_outcome(**kwargs)
    def system_status(self): return self.system_orchestrator.status()
    def diagnose(self): return self.diagnostics.run()
    def validate_system(self): return self.system_validation.run()
    def learn_verified(self, objective, evidence): return self.knowledge_learning.learn(objective, evidence)
    def plan_system_change(self, objective, scope=None): return self.system_developer.plan(objective, scope)
    def self_improvement_assess(self): return self.self_improvement.assess()
    def self_improvement_prepare(self, objective, scope=None): return self.self_improvement.prepare(objective, scope)
    def self_improvement_execute(self, plan, *, approved=False): return self.self_improvement.execute_and_verify(plan, approved=approved)
    def economic_snapshot(self): return self.economic_feedback.snapshot()
    def economic_learning_context(self): return self.economic_feedback.learning_context()
    def generate(self, prompt, *, action="engine.generate", actor_id="engine"):
        if self.model_gateway is None: raise RuntimeError("AURELIX_MODEL_BASE_URL is not configured")
        return self.model_gateway.generate(GenerationRequest(prompt=prompt, action=action, actor_id=actor_id))
