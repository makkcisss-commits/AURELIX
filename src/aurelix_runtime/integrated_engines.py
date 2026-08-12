"""Integrated AURELIX engine implementations.

These implementations are deliberately provider-agnostic. They provide a
working end-to-end control/data flow while external model, search, payment,
and deployment providers remain explicit adapters behind policy checks.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Evidence:
    source: str
    claim: str
    confidence: float = 0.0
    verified: bool = False


@dataclass
class KnowledgeItem:
    id: str
    title: str
    content: str
    evidence: List[Evidence] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=now)


@dataclass
class Experiment:
    id: str
    hypothesis: str
    success_criteria: List[str]
    status: str = "proposed"
    result: Optional[Dict[str, Any]] = None


@dataclass
class Opportunity:
    id: str
    title: str
    rationale: str
    estimated_cost: float = 0.0
    estimated_revenue: float = 0.0
    risk: float = 0.0
    confidence: float = 0.0
    status: str = "proposed"


class EngineStore:
    """Small durable-model boundary; production storage is supplied by adapter."""

    def __init__(self) -> None:
        self.knowledge: Dict[str, KnowledgeItem] = {}
        self.experiments: Dict[str, Experiment] = {}
        self.opportunities: Dict[str, Opportunity] = {}
        self.audit: List[Dict[str, Any]] = []

    def record(self, event: str, **data: Any) -> None:
        self.audit.append({"id": str(uuid4()), "time": now(), "event": event, **data})


class ResearchEngine:
    name = "research"

    def __init__(self, provider: Optional[Callable[[str], List[Evidence]]] = None):
        self.provider = provider

    def run(self, objective: str, store: EngineStore) -> Dict[str, Any]:
        evidence = self.provider(objective) if self.provider else []
        store.record("research.completed", objective=objective, evidence_count=len(evidence))
        return {"objective": objective, "evidence": evidence}


class AcademyEngine:
    name = "academy"

    def run(self, research: Dict[str, Any], store: EngineStore) -> Dict[str, Any]:
        evidence = research.get("evidence", [])
        lessons = [e.claim for e in evidence if getattr(e, "verified", False)]
        store.record("academy.learned", lesson_count=len(lessons))
        return {"lessons": lessons, "gaps": [] if lessons else [research.get("objective", "unknown")]}


class KnowledgeEngine:
    name = "knowledge"

    def run(self, academy: Dict[str, Any], store: EngineStore) -> Dict[str, Any]:
        item = KnowledgeItem(
            id=str(uuid4()),
            title="AURELIX learning record",
            content="\n".join(academy.get("lessons", [])),
            tags=["academy", "learning"],
        )
        store.knowledge[item.id] = item
        store.record("knowledge.stored", knowledge_id=item.id)
        return {"knowledge_id": item.id, "lessons": academy.get("lessons", [])}


class InnovationEngine:
    name = "innovation"

    def run(self, knowledge: Dict[str, Any], store: EngineStore) -> Dict[str, Any]:
        proposal = {
            "id": str(uuid4()),
            "title": "Innovation proposal from validated knowledge",
            "basis": knowledge.get("knowledge_id"),
            "status": "proposal",
        }
        store.record("innovation.proposed", proposal_id=proposal["id"])
        return proposal


class ExperimentEngine:
    name = "experiment"

    def run(self, innovation: Dict[str, Any], store: EngineStore) -> Dict[str, Any]:
        exp = Experiment(
            id=str(uuid4()),
            hypothesis=innovation.get("title", "unknown"),
            success_criteria=["defined", "measured", "reproducible"],
        )
        store.experiments[exp.id] = exp
        store.record("experiment.proposed", experiment_id=exp.id)
        return {"experiment_id": exp.id, "status": exp.status, "criteria": exp.success_criteria}


class EvaluationEngine:
    name = "evaluation"

    def run(self, experiment: Dict[str, Any], store: EngineStore) -> Dict[str, Any]:
        # No claim of success without actual experiment evidence.
        result = {"experiment_id": experiment["experiment_id"], "passed": False, "reason": "awaiting_execution"}
        store.record("evaluation.completed", **result)
        return result


class OpportunityEngine:
    name = "opportunity"

    def run(self, evaluation: Dict[str, Any], store: EngineStore) -> Dict[str, Any]:
        opportunity = Opportunity(
            id=str(uuid4()),
            title="Opportunity candidate",
            rationale="Generated from evaluated evidence; requires validation.",
            confidence=0.0,
        )
        store.opportunities[opportunity.id] = opportunity
        store.record("opportunity.proposed", opportunity_id=opportunity.id)
        return {"opportunity_id": opportunity.id, "status": opportunity.status}


class BusinessEngine:
    name = "business"

    def __init__(self, require_approval: bool = True):
        self.require_approval = require_approval

    def run(self, opportunity: Dict[str, Any], approved: bool = False) -> Dict[str, Any]:
        if self.require_approval and not approved:
            return {"status": "awaiting_approval", "opportunity_id": opportunity.get("opportunity_id")}
        return {"status": "ready_for_execution", "opportunity_id": opportunity.get("opportunity_id")}
