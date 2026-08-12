from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import uuid4


class Outcome(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True)
class Learning:
    learning_id: str
    experiment_id: str
    outcome: Outcome
    observation: str
    evidence_refs: tuple[str, ...]
    confidence: float


class LearningEngine:
    """Turns measured experiment outcomes into explicit, traceable learnings."""

    def __init__(self) -> None:
        self._items: dict[str, Learning] = {}

    def record(self, *, experiment_id: str, outcome: Outcome,
               observation: str, evidence_refs: list[str], confidence: float) -> Learning:
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if not observation.strip():
            raise ValueError("observation is required")
        item = Learning(str(uuid4()), experiment_id, outcome, observation,
                        tuple(evidence_refs), confidence)
        self._items[item.learning_id] = item
        return item

    def get(self, learning_id: str) -> Learning:
        return self._items[learning_id]
