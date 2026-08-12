from __future__ import annotations

from dataclasses import dataclass
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
    """Curates traceable learnings into reusable internal knowledge."""

    def __init__(self) -> None:
        self._knowledge: dict[str, Knowledge] = {}

    def create_knowledge(self, *, title: str, summary: str,
                         learning_refs: list[str], source_refs: list[str],
                         confidence: float) -> Knowledge:
        if not title.strip() or not summary.strip():
            raise ValueError("title and summary are required")
        if not learning_refs:
            raise ValueError("knowledge must reference at least one learning")
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        item = Knowledge(str(uuid4()), title, summary, tuple(learning_refs),
                         tuple(source_refs), confidence)
        self._knowledge[item.knowledge_id] = item
        return item

    def get(self, knowledge_id: str) -> Knowledge:
        return self._knowledge[knowledge_id]
