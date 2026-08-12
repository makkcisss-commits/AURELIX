"""Governed transition checks for provenance and auditability."""
from __future__ import annotations

from dataclasses import dataclass

from .provenance import ProvenanceLedger


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

    def __init__(self, ledger: ProvenanceLedger | None = None):
        self.ledger = ledger or ProvenanceLedger()
        self.audit: list[Transition] = []

    def authorize(self, transition: Transition) -> Transition:
        if transition.object_type in self.REQUIRED_TYPES and not transition.parent_ids:
            raise GovernanceError("governed object requires provenance parents")
        for parent_id in transition.parent_ids:
            if not self.ledger.for_subject(parent_id):
                raise GovernanceError(f"missing provenance parent: {parent_id}")
        self.audit.append(transition)
        return transition

    def register(self, transition: Transition):
        self.authorize(transition)
        return self.ledger.append(
            transition.object_type,
            transition.object_id,
            list(transition.parent_ids),
            actor_id=transition.actor_id,
            action=transition.action,
        )

    def lineage(self, object_id: str):
        return self.ledger.lineage(object_id)
