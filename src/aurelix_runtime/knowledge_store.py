"""Durable knowledge repository boundary for AURELIX."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

from .integrated_engines import KnowledgeItem


@dataclass(frozen=True)
class KnowledgeQuery:
    text: str
    tags: tuple[str, ...] = ()
    limit: int = 20


class KnowledgeRepository:
    def put(self, item: KnowledgeItem) -> None:
        raise NotImplementedError

    def get(self, item_id: str) -> KnowledgeItem | None:
        raise NotImplementedError

    def search(self, query: KnowledgeQuery) -> List[KnowledgeItem]:
        raise NotImplementedError

    def count(self) -> int:
        raise NotImplementedError


class InMemoryKnowledgeRepository(KnowledgeRepository):
    def __init__(self) -> None:
        self._items: Dict[str, KnowledgeItem] = {}

    def put(self, item: KnowledgeItem) -> None:
        self._items[item.id] = item

    def get(self, item_id: str) -> KnowledgeItem | None:
        return self._items.get(item_id)

    def search(self, query: KnowledgeQuery) -> List[KnowledgeItem]:
        text = query.text.lower().strip()
        tags = set(query.tags)
        matches: Iterable[KnowledgeItem] = self._items.values()
        if text:
            matches = (x for x in matches if text in (x.title + " " + x.content).lower())
        if tags:
            matches = (x for x in matches if tags.intersection(x.tags))
        return list(matches)[: max(0, query.limit)]

    def count(self) -> int:
        return len(self._items)
