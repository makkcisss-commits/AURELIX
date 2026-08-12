"""Research-to-knowledge integration with explicit evidence provenance."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from .integrated_engines import Evidence, KnowledgeItem
from .knowledge_store import KnowledgeRepository


@dataclass(frozen=True)
class ResearchKnowledgeResult:
    query: str
    evidence: tuple[Evidence, ...]
    knowledge_ids: tuple[str, ...]


class ResearchToKnowledge:
    """Persist every retrieved source as a traceable knowledge item.

    Retrieved evidence remains unverified unless the research provider marks it
    verified. This adapter never upgrades confidence or verification itself.
    """

    def __init__(self, research_provider, knowledge: KnowledgeRepository):
        self.research_provider = research_provider
        self.knowledge = knowledge

    def research_and_store(self, query: str) -> ResearchKnowledgeResult:
        if not query.strip():
            raise ValueError("query is required")
        evidence = tuple(self.research_provider(query))
        ids: list[str] = []
        now = datetime.now(timezone.utc).isoformat()
        for item in evidence:
            knowledge_id = str(uuid4())
            verification = "verified" if item.verified else "unverified"
            knowledge = KnowledgeItem(
                id=knowledge_id,
                title=f"Research evidence: {item.source}",
                content=item.claim,
                evidence=[item],
                tags=["research", verification],
                created_at=now,
            )
            self.knowledge.put(knowledge)
            ids.append(knowledge_id)
        return ResearchKnowledgeResult(query, evidence, tuple(ids))
