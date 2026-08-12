"""Safe first-party adapters connecting the engineering-loop engines.

These adapters are intentionally deterministic at the runtime boundary. Real
LLM/search providers can be plugged in behind them without giving providers
implicit execution authority.
"""
from dataclasses import dataclass
from typing import Callable

from .engine_contracts import EngineContext, EngineName

Handler = Callable[[EngineContext], EngineContext]


@dataclass
class EngineAdapter:
    name: EngineName
    handler: Handler
    read_only: bool = True

    def run(self, context: EngineContext) -> EngineContext:
        return self.handler(context)


def governor(context: EngineContext) -> EngineContext:
    context.data.setdefault("governance", {"status": "reviewed", "business_enabled": False})
    return context


def research(context: EngineContext) -> EngineContext:
    context.data.setdefault("research", {"status": "ready", "sources": []})
    context.data["research"]["objective"] = context.objective
    return context


def academy(context: EngineContext) -> EngineContext:
    research_state = context.data.get("research", {})
    context.data["academy"] = {
        "status": "learning",
        "knowledge_gaps": [] if research_state.get("sources") else [context.objective],
    }
    return context


def knowledge(context: EngineContext) -> EngineContext:
    context.data["knowledge"] = {
        "evidence_count": len(context.evidence),
        "lessons_count": len(context.lessons),
    }
    return context


def innovation(context: EngineContext) -> EngineContext:
    context.propose("innovation", {"objective": context.objective, "status": "candidate"})
    return context


def experiment(context: EngineContext) -> EngineContext:
    context.data["experiment"] = {"status": "sandbox_required", "executed": False}
    return context


def evaluation(context: EngineContext) -> EngineContext:
    context.data["evaluation"] = {"status": "pending_measurement", "passed": False}
    return context


def opportunity(context: EngineContext) -> EngineContext:
    context.propose("opportunity", {"objective": context.objective, "status": "candidate"})
    return context


def business(context: EngineContext) -> EngineContext:
    # This adapter is deliberately proposal-only. External business actions
    # require the separate approval/authorization layer.
    context.propose("business", {"objective": context.objective, "status": "approval_required"})
    return context


def default_adapters() -> dict[EngineName, EngineAdapter]:
    return {
        EngineName.GOVERNOR: EngineAdapter(EngineName.GOVERNOR, governor),
        EngineName.RESEARCH: EngineAdapter(EngineName.RESEARCH, research),
        EngineName.ACADEMY: EngineAdapter(EngineName.ACADEMY, academy),
        EngineName.KNOWLEDGE: EngineAdapter(EngineName.KNOWLEDGE, knowledge),
        EngineName.INNOVATION: EngineAdapter(EngineName.INNOVATION, innovation),
        EngineName.EXPERIMENT: EngineAdapter(EngineName.EXPERIMENT, experiment),
        EngineName.EVALUATION: EngineAdapter(EngineName.EVALUATION, evaluation),
        EngineName.OPPORTUNITY: EngineAdapter(EngineName.OPPORTUNITY, opportunity),
        EngineName.BUSINESS: EngineAdapter(EngineName.BUSINESS, business),
    }
