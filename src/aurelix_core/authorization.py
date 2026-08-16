from __future__ import annotations

from dataclasses import dataclass

from .identity import Identity, IdentityStatus


class AuthorizationDenied(PermissionError):
    """Raised when an authenticated identity lacks the exact requested scope."""


@dataclass(frozen=True)
class Capability:
    resource: str
    operation: str
    target_scope: str


class AuthorizationPolicy:
    """Deterministic resource/operation/scope policy.

    Authentication proves who the caller is; this policy decides what that
    identity may do. Missing or ambiguous scope always fails closed.
    """

    def __init__(self, capabilities: dict[str, frozenset[Capability]]):
        self._capabilities = capabilities

    def authorize(self, identity: Identity, resource: str, operation: str, target_scope: str) -> None:
        if identity.status is not IdentityStatus.ACTIVE:
            raise AuthorizationDenied("identity_not_active")
        if not resource or not operation or not target_scope:
            raise AuthorizationDenied("scope_required")

        allowed = self._capabilities.get(identity.id, frozenset())
        requested = Capability(resource, operation, target_scope)
        if requested not in allowed:
            raise AuthorizationDenied("scope_denied")


def owner_read_only_policy(identity_id: str) -> AuthorizationPolicy:
    """Explicitly grant only the private API operations exposed by the owner role."""
    resources = {
        Capability("control", "snapshot", "private"),
        Capability("control", "experiments.read", "private"),
        Capability("control", "knowledge.read", "private"),
        Capability("control", "audit.read", "private"),
        Capability("control", "autonomy.read", "private"),
        Capability("control", "diagnostics.read", "private"),
        Capability("control", "validation.read", "private"),
        Capability("actions", "research.execute", "private"),
        Capability("actions", "experiments.execute", "private"),
        Capability("actions", "objectives.submit", "private"),
        Capability("actions", "economic.outcome.record", "private"),
    }
    return AuthorizationPolicy({identity_id: frozenset(resources)})
