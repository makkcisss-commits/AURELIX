"""Research-to-knowledge integration with explicit evidence provenance."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from aurelix_core.governor import Governor
from aurelix_core.models import ActionClass, Actor, AutonomyLevel, DecisionRequest
from .integrated_engines import Evidence, KnowledgeItem
from .knowledge_store import KnowledgeRepository

@dataclass(frozen=True)
class ResearchKnowledgeResult:
    query: str
    evidence: tuple[Evidence, ...]
    knowledge_ids: tuple[str, ...]

class ResearchToKnowledge:
    """Persist retrieved sources only after the canonical Governor allows research."""

    def __init__(self, research_provider, knowledge: KnowledgeRepository, governor: Governor):
        if governor is None:
            raise ValueError("research-to-knowledge requires the canonical governor")
        self.research_provider = research_provider
        self.knowledge = knowledge
        self.governor = governor

    def research_and_store(self, query: str) -> ResearchKnowledgeResult:
        if not query.strip():
            raise ValueError("query is required")
        request = DecisionRequest(
            actor=Actor(id="research-knowledge-adapter", role="research", autonomy=AutonomyLevel.A1),
            action=ActionClass.RESEARCH,
            reason="retrieve and persist research evidence",
            payload={"query": query},
        )
        decision = self.governor.evaluate(request)
        if not decision.allowed:
            raise PermissionError(f"research persistence denied by Governor: {decision.reason}")
        evidence = tuple(self.research_provider(query))
        ids: list[str] = []
        now = datetime.now(timezone.utc).isoformat()
        for item in evidence:
            knowledge_id = str(uuid4())
            verification = "verified" if item.verified else "unverified"
            knowledge = KnowledgeItem(id=knowledge_id, title=f"Research evidence: {item.source}", content=item.claim, evidence=[item], tags=["research", verification], created_at=now)
            self.knowledge.put(knowledge)
            ids.append(knowledge_id)
        return ResearchKnowledgeResult(query, evidence, tuple(ids))
