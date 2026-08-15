from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .identity import Identity


class Permission(str, Enum):
    READ_CONTROL = "control:read"
    READ_AUDIT = "audit:read"
    EXECUTE_RESEARCH = "research:execute"
    EXECUTE_EXPERIMENT = "experiment:execute"


@dataclass(frozen=True)
class AuthorizationPolicy:
    """Central role-to-permission policy. Authentication never implies access."""

    permissions_by_role: dict[str, frozenset[Permission]]

    @classmethod
    def owner_only(cls) -> "AuthorizationPolicy":
        return cls({"owner": frozenset(Permission)})

    def allows(self, identity: Identity, permission: Permission) -> bool:
        return permission in self.permissions_by_role.get(identity.role, frozenset())


def require_permission(identity: Identity, permission: Permission, policy: AuthorizationPolicy) -> None:
    if not policy.allows(identity, permission):
        raise PermissionError("permission denied")
