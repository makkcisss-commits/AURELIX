"""Identity/policy boundary used before governed transitions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet


class PolicyDenied(RuntimeError):
    pass


@dataclass(frozen=True)
class AgentIdentity:
    agent_id: str
    roles: FrozenSet[str] = frozenset()


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


class AgentPolicy:
    def decide(self, identity: AgentIdentity, object_type: str, action: str) -> PolicyDecision:
        if not identity.agent_id:
            return PolicyDecision(False, "missing agent identity")
        if action == "execute_business" and "business_operator" not in identity.roles:
            return PolicyDecision(False, "business execution role required")
        return PolicyDecision(True, "policy allows transition")

    def require(self, identity: AgentIdentity, object_type: str, action: str) -> None:
        decision = self.decide(identity, object_type, action)
        if not decision.allowed:
            raise PolicyDenied(decision.reason)
