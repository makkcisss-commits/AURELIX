"""Durable knowledge repository boundary for AURELIX.

The repository API is intentionally storage-agnostic.  The SQLite adapter uses
AURELIX's RuntimeStore database so knowledge survives process restarts without
creating a second persistence system.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from typing import Dict, Iterable, List

from .integrated_engines import Evidence, KnowledgeItem


class KnowledgeQuery:
    def __init__(self, text: str, tags: tuple[str, ...] = (), limit: int = 20) -> None:
        self.text = text
        self.tags = tags
        self.limit = max(0, min(int(limit), 500))


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
        return list(matches)[: query.limit]

    def count(self) -> int:
        return len(self._items)


class SQLiteKnowledgeRepository(KnowledgeRepository):
    """Durable repository backed by the same SQLite connection as RuntimeStore."""

    def __init__(self, runtime_store) -> None:
        self.store = runtime_store
        with self.store.lock, self.store.db:
            self.store.db.execute(
                """CREATE TABLE IF NOT EXISTS knowledge_items (
                    item_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    evidence TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )"""
            )
            self.store.db.execute(
                "CREATE INDEX IF NOT EXISTS idx_knowledge_items_created ON knowledge_items(created_at)"
            )

    @staticmethod
    def _encode(item: KnowledgeItem) -> tuple:
        payload = asdict(item)
        return (
            item.id,
            item.title,
            item.content,
            json.dumps(payload["evidence"], sort_keys=True),
            json.dumps(item.tags, sort_keys=True),
            item.created_at,
        )

    @staticmethod
    def _decode(row) -> KnowledgeItem:
        evidence = [Evidence(**value) for value in json.loads(row[3])]
        return KnowledgeItem(
            id=row[0],
            title=row[1],
            content=row[2],
            evidence=evidence,
            tags=json.loads(row[4]),
            created_at=row[5],
        )

    def put(self, item: KnowledgeItem) -> None:
        encoded = self._encode(item)
        with self.store.lock, self.store.db:
            self.store.db.execute(
                """INSERT INTO knowledge_items
                   (item_id,title,content,evidence,tags,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,datetime('now'))
                   ON CONFLICT(item_id) DO UPDATE SET
                     title=excluded.title,
                     content=excluded.content,
                     evidence=excluded.evidence,
                     tags=excluded.tags,
                     updated_at=datetime('now')""",
                encoded,
            )

    def get(self, item_id: str) -> KnowledgeItem | None:
        with self.store.lock:
            row = self.store.db.execute(
                "SELECT item_id,title,content,evidence,tags,created_at FROM knowledge_items WHERE item_id=?",
                (item_id,),
            ).fetchone()
        return self._decode(row) if row else None

    def search(self, query: KnowledgeQuery) -> List[KnowledgeItem]:
        text = query.text.strip().lower()
        tags = set(query.tags)
        with self.store.lock:
            rows = self.store.db.execute(
                "SELECT item_id,title,content,evidence,tags,created_at FROM knowledge_items ORDER BY created_at DESC LIMIT ?",
                (max(query.limit * 5, query.limit),),
            ).fetchall()
        items = [self._decode(row) for row in rows]
        if text:
            items = [x for x in items if text in (x.title + " " + x.content).lower()]
        if tags:
            items = [x for x in items if tags.intersection(x.tags)]
        return items[: query.limit]

    def count(self) -> int:
        with self.store.lock:
            row = self.store.db.execute("SELECT COUNT(*) FROM knowledge_items").fetchone()
        return int(row[0])
