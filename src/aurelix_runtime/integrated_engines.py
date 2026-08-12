"""Integrated AURELIX engine implementations.

These implementations are provider-agnostic. External model, search, payment,
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
    success_criteria: List[dict[str, Any]]
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
        objective = objective.strip()
        if not objective:
            raise ValueError("research objective is required")
        evidence = self.provider(objective) if self.provider else []
        store.record("research.completed", objective=objective, evidence_count=len(evidence))
        return {"objective": objective, "evidence": evidence}


class AcademyEngine:
    name = "academy"

    def __init__(self, model_gateway=None):
        self.model_gateway = model_gateway

    def run(self, research: Dict[str, Any], store: EngineStore) -> Dict[str, Any]:
        evidence = list(research.get("evidence", []))
        lessons = [e.claim for e in evidence if getattr(e, "verified", False)]
        if self.model_gateway and evidence:
            from aurelix_core.model_gateway import GenerationRequest
            source_text = "\n".join(f"- {e.source}: {e.claim}" for e in evidence)
            generated = self.model_gateway.generate(
                GenerationRequest(
                    prompt=("Synthesize the following source-backed research into concise lessons. "
                            "Do not invent claims and explicitly preserve uncertainty.\n" + source_text),
                    action="academy.synthesize",
                    actor_id="academy",
                )
            )
            if generated.strip():
                lessons = [generated.strip()]
        store.record("academy.learned", lesson_count=len(lessons), evidence_count=len(evidence))
        return {
            "lessons": lessons,
            "evidence": evidence,
            "gaps": [] if lessons else [research.get("objective", "unknown")],
        }


class KnowledgeEngine:
    name = "knowledge"

    def run(self, academy: Dict[str, Any], store: EngineStore) -> Dict[str, Any]:
        evidence = list(academy.get("evidence", []))
        verified = bool(evidence) and all(getattr(item, "verified", False) for item in evidence)
        tags = ["academy", "learning", "validated" if verified else "draft"]
        item = KnowledgeItem(
            id=str(uuid4()),
            title="AURELIX learning record",
            content="\n".join(academy.get("lessons", [])),
            evidence=evidence,
            tags=tags,
        )
        store.knowledge[item.id] = item
        store.record("knowledge.stored", knowledge_id=item.id, evidence_count=len(evidence), validated=verified)
        return {
            "knowledge_id": item.id,
            "lessons": academy.get("lessons", []),
            "evidence": evidence,
            "validated": verified,
        }


class InnovationEngine:
    name = "innovation"

    def __init__(self, model_gateway=None):
        self.model_gateway = model_gateway

    def run(self, knowledge: Dict[str, Any], store: EngineStore) -> Dict[str, Any]:
        evidence = list(knowledge.get("evidence", []))
        if self.model_gateway:
            from aurelix_core.model_gateway import GenerationRequest
            evidence_text = "\n".join(
                f"- {getattr(item, 'source', '')}: {getattr(item, 'claim', '')}"
                for item in evidence
            )
            result = self.model_gateway.structured_output(
                GenerationRequest(
                    prompt=("Generate one conservative innovation proposal from this knowledge. "
                            "Do not invent evidence. Preserve the supplied provenance.\n"
                            + str(knowledge) + "\nEvidence:\n" + evidence_text),
                    action="innovation.propose",
                    actor_id="innovation",
                ),
                {
                    "title": "string",
                    "problem": "string",
                    "proposed_solution": "string",
                    "expected_value": "string",
                    "estimated_cost": "number",
                    "risk": "integer",
                    "confidence": "number",
                },
            )
            proposal = {
                "id": str(uuid4()),
                "basis": knowledge.get("knowledge_id"),
                "evidence_count": len(evidence),
                **result,
            }
        else:
            proposal = {
                "id": str(uuid4()),
                "title": "Innovation proposal from validated knowledge",
                "basis": knowledge.get("knowledge_id"),
                "evidence_count": len(evidence),
                "status": "proposal",
            }
        store.record("innovation.proposed", proposal_id=proposal["id"], evidence_count=proposal["evidence_count"])
        return proposal


class ExperimentEngine:
    name = "experiment"

    def run(self, innovation: Dict[str, Any], store: EngineStore) -> Dict[str, Any]:
        exp = Experiment(
            id=str(uuid4()),
            hypothesis=innovation.get("proposed_solution", innovation.get("title", "unknown")),
            success_criteria=[{"metric": "success", "operator": ">=", "target": 1.0}],
        )
        store.experiments[exp.id] = exp
        store.record("experiment.proposed", experiment_id=exp.id)
        return {"experiment_id": exp.id, "status": exp.status, "criteria": exp.success_criteria}


class EvaluationEngine:
    name = "evaluation"

    def run(self, experiment: Dict[str, Any], store: EngineStore) -> Dict[str, Any]:
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
