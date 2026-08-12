from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ScopeDenied(Exception):
    """Raised when an actor attempts an operation outside its declared scope."""


class ResourceKind(str, Enum):
    RESEARCH = "research"
    KNOWLEDGE = "knowledge"
    EXPERIMENT = "experiment"
    BUILD = "build"
    BUSINESS = "business"
    REVENUE = "revenue"
    TREASURY = "treasury"
    GOVERNOR = "governor"
    SECRETS = "secrets"
    PRODUCTION = "production"


@dataclass(frozen=True)
class ResourcePermission:
    actor_id: str
    resource: ResourceKind
    operations: frozenset[str]
    scope: str

    def allows(self, actor_id: str, resource: ResourceKind, operation: str, target_scope: str) -> bool:
        if actor_id != self.actor_id or resource != self.resource:
            return False
        if operation not in self.operations:
            return False
        return target_scope == self.scope or self.scope == "*"


@dataclass(frozen=True)
class ResourceRequest:
    actor_id: str
    resource: ResourceKind
    operation: str
    target_scope: str


def authorize_resource(request: ResourceRequest, permission: ResourcePermission) -> None:
    if not permission.allows(
        request.actor_id,
        request.resource,
        request.operation,
        request.target_scope,
    ):
        raise ScopeDenied("resource operation is outside the actor scope")
