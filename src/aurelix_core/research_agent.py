from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .research import ResearchEngine, ResearchFinding, ResearchSource


class ResearchAgentStage(str, Enum):
    PLAN = "PLAN"
    RETRIEVE = "RETRIEVE"
    VERIFY = "VERIFY"
    SYNTHESIZE = "SYNTHESIZE"
    REPORT = "REPORT"


@dataclass(frozen=True)
class ResearchPlan:
    question: str
    subquestions: tuple[str, ...]
    source_policy: str


@dataclass(frozen=True)
class ResearchReport:
    question: str
    findings: tuple[ResearchFinding, ...]
    limitations: tuple[str, ...]


class ResearchAgent:
    """Orchestration shell for a tool-backed, evidence-first research agent.

    The model may plan and synthesize, but retrieval is performed by explicit
    adapters and every accepted finding must reference stored sources.
    """

    def __init__(self, engine: ResearchEngine) -> None:
        self.engine = engine

    def plan(self, question: str, subquestions: list[str], source_policy: str) -> ResearchPlan:
        if not question.strip() or not subquestions:
            raise ValueError("question and subquestions are required")
        return ResearchPlan(question, tuple(subquestions), source_policy)

    def register_sources(self, sources: list[ResearchSource]) -> None:
        for source in sources:
            self.engine.add_source(source)

    def synthesize(self, *, plan: ResearchPlan, findings: list[ResearchFinding],
                   limitations: list[str]) -> ResearchReport:
        if not findings:
            raise ValueError("cannot synthesize a report without findings")
        if any(f.query != plan.question for f in findings):
            raise ValueError("finding query does not match research plan")
        return ResearchReport(plan.question, tuple(findings), tuple(limitations))
