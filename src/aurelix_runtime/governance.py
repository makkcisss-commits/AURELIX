"""Governed transition checks for provenance, identity, policy and audit."""
from __future__ import annotations

from dataclasses import dataclass

from .agent_policy import AgentIdentity, AgentPolicy
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
    """Require lineage and policy authorization before governed transitions."""

    REQUIRED_TYPES = {"evidence", "knowledge", "experiment", "evaluation", "opportunity"}

    def __init__(self, ledger: ProvenanceLedger | None = None, policy: AgentPolicy | None = None):
        self.ledger = ledger or ProvenanceLedger()
        self.policy = policy or AgentPolicy()
        self.audit: list[Transition] = []

    def authorize(self, transition: Transition, identity: AgentIdentity | None = None) -> Transition:
        if transition.object_type in self.REQUIRED_TYPES and not transition.parent_ids:
            raise GovernanceError("governed object requires provenance parents")
        for parent_id in transition.parent_ids:
            if not self.ledger.for_subject(parent_id):
                raise GovernanceError(f"missing provenance parent: {parent_id}")
        identity = identity or AgentIdentity(transition.actor_id)
        if identity.agent_id != transition.actor_id:
            raise GovernanceError("actor identity does not match transition actor")
        try:
            self.policy.require(identity, transition.object_type, transition.action)
        except Exception as exc:
            raise GovernanceError(str(exc)) from exc
        self.audit.append(transition)
        return transition

    def register(self, transition: Transition, identity: AgentIdentity | None = None):
        self.authorize(transition, identity)
        return self.ledger.append(
            transition.object_type,
            transition.object_id,
            list(transition.parent_ids),
            actor_id=transition.actor_id,
            action=transition.action,
        )

    def lineage(self, object_id: str):
        return self.ledger.lineage(object_id)
