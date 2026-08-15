"""Canonical capability registry and provider selection boundary.

The control plane is intentionally small: it does not execute providers. It
normalizes capability names, tracks explicit provider metadata, and refuses to
select providers that are disabled, unavailable, or unauthorized.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CapabilityStatus(str, Enum):
    RESOLVED = "resolved"
    BLOCKED = "blocked"
    MISSING = "missing"
    LEARNING_REQUIRED = "learning_required"
    UNAUTHORIZED = "unauthorized"
    UNAVAILABLE = "unavailable"


class ProviderKind(str, Enum):
    AGENT = "agent"
    TOOL = "tool"
    SERVICE = "service"


@dataclass(frozen=True)
class CapabilityProvider:
    provider_id: str
    capability: str
    kind: ProviderKind
    enabled: bool = True
    available: bool = True
    authorized: bool = True
    priority: int = 0


@dataclass(frozen=True)
class CapabilityResolution:
    capability: str
    status: CapabilityStatus
    providers: tuple[CapabilityProvider, ...] = ()
    reason: str | None = None


class CapabilityControlPlane:
    """Resolve capabilities without silently dropping unresolved dependencies."""

    def __init__(self) -> None:
        self._providers: dict[str, dict[str, CapabilityProvider]] = {}

    @staticmethod
    def normalize(capability: str) -> str:
        normalized = " ".join(str(capability).strip().casefold().replace("_", "-").split())
        if not normalized:
            raise ValueError("capability is required")
        return normalized

    def register(self, provider: CapabilityProvider) -> CapabilityProvider:
        capability = self.normalize(provider.capability)
        if not provider.provider_id.strip():
            raise ValueError("provider_id is required")
        normalized = CapabilityProvider(
            provider_id=provider.provider_id.strip(),
            capability=capability,
            kind=provider.kind,
            enabled=provider.enabled,
            available=provider.available,
            authorized=provider.authorized,
            priority=provider.priority,
        )
        self._providers.setdefault(capability, {})[normalized.provider_id] = normalized
        return normalized

    def unregister(self, provider_id: str, capability: str) -> None:
        key = self.normalize(capability)
        providers = self._providers.get(key)
        if not providers:
            return
        providers.pop(provider_id, None)
        if not providers:
            self._providers.pop(key, None)

    def resolve(self, capability: str) -> CapabilityResolution:
        key = self.normalize(capability)
        providers = tuple(self._providers.get(key, {}).values())
        if not providers:
            return CapabilityResolution(key, CapabilityStatus.MISSING, reason="no provider is registered")
        if not any(p.enabled for p in providers):
            return CapabilityResolution(key, CapabilityStatus.BLOCKED, providers, "all providers are disabled")
        enabled = tuple(p for p in providers if p.enabled)
        if not any(p.authorized for p in enabled):
            return CapabilityResolution(key, CapabilityStatus.UNAUTHORIZED, enabled, "no enabled provider is authorized")
        authorized = tuple(p for p in enabled if p.authorized)
        if not any(p.available for p in authorized):
            return CapabilityResolution(key, CapabilityStatus.UNAVAILABLE, authorized, "no authorized provider is available")
        available = tuple(sorted((p for p in authorized if p.available), key=lambda p: (-p.priority, p.provider_id)))
        return CapabilityResolution(key, CapabilityStatus.RESOLVED, available)

    def select(self, capability: str) -> CapabilityProvider:
        resolution = self.resolve(capability)
        if resolution.status is not CapabilityStatus.RESOLVED:
            raise RuntimeError(f"capability {resolution.capability!r} is {resolution.status.value}: {resolution.reason}")
        return resolution.providers[0]
