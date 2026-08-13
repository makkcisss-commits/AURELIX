"""Integrated AURELIX engine implementations with optional durable state."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
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
    """Engine state with an optional RuntimeStore durability boundary."""

    def __init__(self, runtime_store=None) -> None:
        self.runtime_store = runtime_store
        self.knowledge: Dict[str, KnowledgeItem] = {}
        self.experiments: Dict[str, Experiment] = {}
        self.opportunities: Dict[str, Opportunity] = {}
        self.audit: List[Dict[str, Any]] = []
        self._load()

    def _read_state(self, key: str) -> Any:
        if self.runtime_store is None:
            return None
        with self.runtime_store.lock:
            row = self.runtime_store.db.execute("SELECT value FROM runtime_state WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def _write_state(self, key: str, value: Any) -> None:
        if self.runtime_store is None:
            return
        with self.runtime_store.lock, self.runtime_store.db:
            self.runtime_store.db.execute(
                "INSERT INTO runtime_state(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, json.dumps(value, sort_keys=True)),
            )

    def _load(self) -> None:
        data = self._read_state("engine.knowledge") or {}
        self.knowledge = {
            item_id: KnowledgeItem(
                id=item["id"], title=item["title"], content=item["content"],
                evidence=[Evidence(**e) for e in item.get("evidence", [])],
                tags=item.get("tags", []), created_at=item.get("created_at", now()),
            ) for item_id, item in data.items()
        }
        data = self._read_state("engine.experiments") or {}
        self.experiments = {k: Experiment(**v) for k, v in data.items()}
        data = self._read_state("engine.opportunities") or {}
        self.opportunities = {k: Opportunity(**v) for k, v in data.items()}
        self.audit = self._read_state("engine.audit") or []

    def _persist(self) -> None:
        self._write_state("engine.knowledge", {
            k: {**asdict(v), "evidence": [asdict(e) for e in v.evidence]}
            for k, v in self.knowledge.items()
        })
        self._write_state("engine.experiments", {k: asdict(v) for k, v in self.experiments.items()})
        self._write_state("engine.opportunities", {k: asdict(v) for k, v in self.opportunities.items()})
        self._write_state("engine.audit", self.audit[-5000:])

    def record(self, event: str, **data: Any) -> None:
        self.audit.append({"id": str(uuid4()), "time": now(), "event": event, **data})
        self._persist()

    def persist(self) -> None:
        self._persist()


class ResearchEngine:
    name = "research"

    def __init__(self, provider: Optional[Callable[[str], List[Evidence]]] = None):
        self.provider = provider

    @property
    def available(self) -> bool:
        return self.provider is not None

    def run(self, objective: str, store: EngineStore) -> Dict[str, Any]:
        objective = objective.strip()
        if not objective:
            raise ValueError("research objective is required")
        if self.provider is None:
            store.record("research.blocked", objective=objective, reason="no_provider")
            return {"objective": objective, "evidence": [], "status": "awaiting_provider", "provider_available": False}
        evidence = self.provider(objective)
        status = "completed" if evidence else "no_evidence"
        store.record("research.completed", objective=objective, evidence_count=len(evidence), status=status)
        return {"objective": objective, "evidence": evidence, "status": status, "provider_available": True}


class AcademyEngine:
    name = "academy"
    def __init__(self, model_gateway=None): self.model_gateway = model_gateway

    def run(self, research: Dict[str, Any], store: EngineStore) -> Dict[str, Any]:
        evidence = list(research.get("evidence", []))
        if research.get("status") == "awaiting_provider":
            store.record("academy.blocked", reason="research_provider_unavailable")
            return {"lessons": [], "evidence": [], "gaps": [research.get("objective", "unknown")], "status": "awaiting_research"}
        lessons = [e.claim for e in evidence if getattr(e, "verified", False)]
        if self.model_gateway and evidence:
            from aurelix_core.model_gateway import GenerationRequest
            source_text = "\n".join(f"- {e.source}: {e.claim}" for e in evidence)
            generated = self.model_gateway.generate(GenerationRequest(
                prompt="Synthesize source-backed research into concise lessons. Do not invent claims and preserve uncertainty.\n" + source_text,
                action="academy.synthesize", actor_id="academy"))
            if generated.strip(): lessons = [generated.strip()]
        store.record("academy.learned", lesson_count=len(lessons), evidence_count=len(evidence))
        return {"lessons": lessons, "evidence": evidence, "gaps": [] if lessons else [research.get("objective", "unknown")], "status": "completed" if lessons else "insufficient_evidence"}


class KnowledgeEngine:
    name = "knowledge"
    def run(self, academy: Dict[str, Any], store: EngineStore) -> Dict[str, Any]:
        evidence = list(academy.get("evidence", []))
        if academy.get("status") in {"awaiting_research", "insufficient_evidence"}:
            store.record("knowledge.blocked", reason=academy.get("status"))
            return {"knowledge_id": None, "lessons": academy.get("lessons", []), "evidence": evidence, "validated": False, "status": "awaiting_evidence"}
        verified = bool(evidence) and all(getattr(item, "verified", False) for item in evidence)
        item = KnowledgeItem(str(uuid4()), "AURELIX learning record", "\n".join(academy.get("lessons", [])), evidence, ["academy", "learning", "validated" if verified else "draft"])
        store.knowledge[item.id] = item
        store.record("knowledge.stored", knowledge_id=item.id, evidence_count=len(evidence), validated=verified)
        return {"knowledge_id": item.id, "lessons": academy.get("lessons", []), "evidence": evidence, "validated": verified, "status": "validated" if verified else "draft"}


class InnovationEngine:
    name = "innovation"
    def __init__(self, model_gateway=None): self.model_gateway = model_gateway

    def run(self, knowledge: Dict[str, Any], store: EngineStore) -> Dict[str, Any]:
        if not knowledge.get("knowledge_id"):
            store.record("innovation.blocked", reason="no_knowledge")
            return {"status": "awaiting_knowledge", "basis": None, "evidence_count": 0}
        evidence = list(knowledge.get("evidence", []))
        if self.model_gateway:
            from aurelix_core.model_gateway import GenerationRequest
            evidence_text = "\n".join(f"- {getattr(e, 'source', '')}: {getattr(e, 'claim', '')}" for e in evidence)
            result = self.model_gateway.structured_output(GenerationRequest(
                prompt="Generate one conservative innovation proposal from this knowledge. Do not invent evidence.\n" + str(knowledge) + "\nEvidence:\n" + evidence_text,
                action="innovation.propose", actor_id="innovation"),
                {"title":"string","problem":"string","proposed_solution":"string","expected_value":"string","estimated_cost":"number","risk":"integer","confidence":"number"})
            proposal = {"id": str(uuid4()), "basis": knowledge.get("knowledge_id"), "evidence_count": len(evidence), **result, "status": "proposal"}
        else:
            proposal = {"id": str(uuid4()), "title": "Innovation proposal from validated knowledge", "basis": knowledge.get("knowledge_id"), "evidence_count": len(evidence), "status": "proposal"}
        store.record("innovation.proposed", proposal_id=proposal["id"], evidence_count=proposal["evidence_count"])
        return proposal


class ExperimentEngine:
    name = "experiment"
    def run(self, innovation: Dict[str, Any], store: EngineStore) -> Dict[str, Any]:
        if innovation.get("status") != "proposal":
            store.record("experiment.blocked", reason=innovation.get("status", "unknown"))
            return {"experiment_id": None, "status": "awaiting_innovation", "criteria": []}
        exp = Experiment(str(uuid4()), innovation.get("proposed_solution", innovation.get("title", "unknown")), [{"metric":"success","operator":">=","target":1.0}])
        store.experiments[exp.id] = exp
        store.record("experiment.proposed", experiment_id=exp.id)
        return {"experiment_id": exp.id, "status": exp.status, "criteria": exp.success_criteria}


class EvaluationEngine:
    name = "evaluation"
    def run(self, experiment: Dict[str, Any], store: EngineStore) -> Dict[str, Any]:
        if not experiment.get("experiment_id"):
            result = {"experiment_id": None, "passed": False, "reason": "awaiting_experiment"}
        else:
            result = {"experiment_id": experiment["experiment_id"], "passed": False, "reason": "awaiting_execution"}
        store.record("evaluation.completed", **result)
        return result


class OpportunityEngine:
    name = "opportunity"
    def run(self, evaluation: Dict[str, Any], store: EngineStore) -> Dict[str, Any]:
        if not evaluation.get("passed"):
            store.record("opportunity.blocked", reason=evaluation.get("reason", "evaluation_failed"))
            return {"opportunity_id": None, "status": "awaiting_validation", "reason": evaluation.get("reason", "evaluation_failed")}
        opportunity = Opportunity(str(uuid4()), "Validated opportunity", "Generated from evaluated evidence.", status="validated", confidence=1.0)
        store.opportunities[opportunity.id] = opportunity
        store.record("opportunity.proposed", opportunity_id=opportunity.id)
        return {"opportunity_id": opportunity.id, "status": opportunity.status, "confidence": opportunity.confidence}


class BusinessEngine:
    name = "business"
    def __init__(self, require_approval: bool = True): self.require_approval = require_approval

    def run(self, opportunity: Dict[str, Any], approved: bool = False) -> Dict[str, Any]:
        opportunity_id = opportunity.get("opportunity_id")
        if not opportunity_id or opportunity.get("status") != "validated":
            return {"status": "awaiting_validation", "opportunity_id": opportunity_id}
        if self.require_approval and not approved:
            return {"status":"awaiting_approval", "opportunity_id":opportunity_id}
        return {"status":"ready_for_execution", "opportunity_id":opportunity_id}
