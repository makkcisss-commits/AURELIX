from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from uuid import uuid4


@dataclass(frozen=True)
class Knowledge:
    knowledge_id: str
    title: str
    summary: str
    learning_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    confidence: float


class AcademyEngine:
    """Canonical Academy knowledge authority with optional durable storage."""

    _STATE_KEY = "academy.knowledge"

    def __init__(self, store=None) -> None:
        self.store = store
        self._knowledge: dict[str, Knowledge] = {}
        self._load()

    def _load(self) -> None:
        if self.store is None:
            return
        with self.store.lock:
            row = self.store.db.execute(
                "SELECT value FROM runtime_state WHERE key=?", (self._STATE_KEY,)
            ).fetchone()
        data = json.loads(row[0]) if row else {}
        self._knowledge = {
            key: Knowledge(
                knowledge_id=value["knowledge_id"],
                title=value["title"],
                summary=value["summary"],
                learning_refs=tuple(value.get("learning_refs", [])),
                source_refs=tuple(value.get("source_refs", [])),
                confidence=float(value["confidence"]),
            )
            for key, value in data.items()
        }

    def _persist(self) -> None:
        if self.store is None:
            return
        payload = {key: asdict(value) for key, value in self._knowledge.items()}
        with self.store.lock, self.store.db:
            self.store.db.execute(
                "INSERT INTO runtime_state(key,value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (self._STATE_KEY, json.dumps(payload, sort_keys=True)),
            )

    def create_knowledge(
        self,
        *,
        title: str,
        summary: str,
        learning_refs: list[str],
        source_refs: list[str],
        confidence: float,
    ) -> Knowledge:
        if not title.strip() or not summary.strip():
            raise ValueError("title and summary are required")
        if not learning_refs:
            raise ValueError("knowledge must reference at least one learning")
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        item = Knowledge(
            str(uuid4()), title, summary, tuple(learning_refs),
            tuple(source_refs), confidence,
        )
        self._knowledge[item.knowledge_id] = item
        self._persist()
        return item

    def get(self, knowledge_id: str) -> Knowledge:
        return self._knowledge[knowledge_id]

    def all(self) -> list[Knowledge]:
        return list(self._knowledge.values())
