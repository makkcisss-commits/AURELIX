"""Optional PostgreSQL knowledge repository.

The dependency is deliberately optional at import time so local SQLite/in-memory
runs do not require PostgreSQL. Configure AURELIX_DATABASE_URL to enable it.
"""
from __future__ import annotations

import json
from typing import List

from .integrated_engines import Evidence, KnowledgeItem
from .knowledge_store import KnowledgeQuery, KnowledgeRepository


class PostgresKnowledgeRepository(KnowledgeRepository):
    def __init__(self, connection_string: str):
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("PostgreSQL support requires psycopg[binary]") from exc
        self._psycopg = psycopg
        self.connection_string = connection_string
        self._ensure_schema()

    def _connect(self):
        return self._psycopg.connect(self.connection_string)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags JSONB NOT NULL,
                    evidence JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_created_at ON knowledge(created_at DESC)")

    def put(self, item: KnowledgeItem) -> None:
        evidence = [{"source": e.source, "claim": e.claim, "confidence": e.confidence, "verified": e.verified} for e in item.evidence]
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO knowledge (id, title, content, tags, evidence, created_at)
                VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s)
                ON CONFLICT (id) DO UPDATE SET title=EXCLUDED.title, content=EXCLUDED.content,
                    tags=EXCLUDED.tags, evidence=EXCLUDED.evidence
            """, (item.id, item.title, item.content, json.dumps(item.tags), json.dumps(evidence), item.created_at))

    def get(self, item_id: str) -> KnowledgeItem | None:
        with self._connect() as conn:
            row = conn.execute("SELECT id,title,content,tags,evidence,created_at FROM knowledge WHERE id=%s", (item_id,)).fetchone()
        return self._from_row(row) if row else None

    def search(self, query: KnowledgeQuery) -> List[KnowledgeItem]:
        with self._connect() as conn:
            if query.text.strip():
                rows = conn.execute("""
                    SELECT id,title,content,tags,evidence,created_at FROM knowledge
                    WHERE to_tsvector('simple', title || ' ' || content) @@ plainto_tsquery('simple', %s)
                    ORDER BY created_at DESC LIMIT %s
                """, (query.text, max(0, query.limit))).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id,title,content,tags,evidence,created_at FROM knowledge ORDER BY created_at DESC LIMIT %s",
                    (max(0, query.limit),),
                ).fetchall()
        return [self._from_row(row) for row in rows if not query.tags or set(query.tags).intersection(row[3])]

    def count(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM knowledge").fetchone()
        return int(row[0])

    @staticmethod
    def _from_row(row) -> KnowledgeItem:
        evidence = [Evidence(str(x["source"]), str(x["claim"]), float(x.get("confidence", 0.0)), bool(x.get("verified", False))) for x in row[4]]
        return KnowledgeItem(str(row[0]), str(row[1]), str(row[2]), evidence, list(row[3]), row[5].isoformat())
