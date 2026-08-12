"""Build bounded research context from validated institutional knowledge."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .knowledge_store import KnowledgeQuery, KnowledgeRepository


@dataclass(frozen=True)
class KnowledgeContext:
    query: str
    items: List[object]

    def as_text(self) -> str:
        return "\n\n".join(
            f"[{getattr(item, 'id', 'unknown')}] {getattr(item, 'title', '')}: {getattr(item, 'content', '')}"
            for item in self.items
        )


class KnowledgeContextBuilder:
    def __init__(self, repository: KnowledgeRepository):
        self.repository = repository

    def build(self, query: str, limit: int = 10) -> KnowledgeContext:
        items = self.repository.search(KnowledgeQuery(query, ("validated",), limit))
        return KnowledgeContext(query, items)
