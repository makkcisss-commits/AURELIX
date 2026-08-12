"""Governed transition checks for provenance and auditability."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .learning_ledger import LearningLedger


class GovernanceError(RuntimeError):
    pass


@dataclass(frozen=True)
class Transition:
    object_id: str
    object_type: str
    parent_ids: tuple[str, ...]
    actor_id: str
    action: str


class GovernanceGate:
    """Require traceable lineage before an object enters a governed stage."""

    REQUIRED_TYPES = {"evidence", "knowledge", "experiment", "evaluation", "opportunity"}

    def __init__(self, ledger: LearningLedger | None = None):
        self.ledger = ledger or LearningLedger()
        self.audit: list[Transition] = []

    def authorize(self, transition: Transition) -> Transition:
        if transition.object_type in self.REQUIRED_TYPES and not transition.parent_ids:
            raise GovernanceError("governed object requires provenance parents")
        if transition.object_type in self.REQUIRED_TYPES:
            for parent_id in transition.parent_ids:
                if self.ledger.ledger.get(parent_id) is None:
                    raise GovernanceError(f"missing provenance parent: {parent_id}")
        self.audit.append(transition)
        return transition

    def lineage(self, object_id: str):
        return self.ledger.ledger.lineage(object_id)
