"""Canonical capability control plane for AURELIX.

The control plane separates capability existence, validation, availability and
authorization.  It is intentionally provider-neutral: agents, tools and
external services can all advertise the same capability contract.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from typing import Iterable


class CapabilityState(str, Enum):
    RESOLVED = "resolved"
    BLOCKED = "blocked"
    MISSING = "missing"
    LEARNING_REQUIRED = "learning_required"
    UNAUTHORIZED = "unauthorized"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class CapabilityProvider:
    provider_id: str
    provider_type: str  # agent | tool | service
    capabilities: frozenset[str]
    enabled: bool = True
    authorized: bool = True


@dataclass(frozen=True)
class CapabilityResolution:
    capability: str
    state: CapabilityState
    providers: tuple[CapabilityProvider, ...] = ()
    reason: str | None = None


class CapabilityControlPlane:
    """Single in-process authority for capability discovery and resolution.

    Registration is deterministic and thread-safe. Resolution never silently
    drops an unknown capability: callers receive an explicit state and reason.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._capabilities: set[str] = set()
        self._providers: dict[str, CapabilityProvider] = {}

    @staticmethod
    def _normalize(value: str) -> str:
        value = value.strip().casefold()
        if not value:
            raise ValueError("capability must not be empty")
        return value

    def register_capability(self, capability: str) -> str:
        normalized = self._normalize(capability)
        with self._lock:
            self._capabilities.add(normalized)
        return normalized

    def register_provider(self, provider: CapabilityProvider) -> None:
        if not provider.provider_id.strip():
            raise ValueError("provider_id must not be empty")
        if provider.provider_type not in {"agent", "tool", "service"}:
            raise ValueError("provider_type must be agent, tool or service")
        capabilities = frozenset(self._normalize(item) for item in provider.capabilities)
        normalized = CapabilityProvider(
            provider_id=provider.provider_id.strip(),
            provider_type=provider.provider_type,
            capabilities=capabilities,
            enabled=provider.enabled,
            authorized=provider.authorized,
        )
        with self._lock:
            self._providers[normalized.provider_id] = normalized
            self._capabilities.update(capabilities)

    def register_providers(self, providers: Iterable[CapabilityProvider]) -> None:
        for provider in providers:
            self.register_provider(provider)

    def resolve(self, capability: str) -> CapabilityResolution:
        normalized = self._normalize(capability)
        with self._lock:
            if normalized not in self._capabilities:
                return CapabilityResolution(normalized, CapabilityState.MISSING, reason="capability is not registered")
            providers = tuple(
                provider for provider in self._providers.values()
                if normalized in provider.capabilities
            )
            if not providers:
                return CapabilityResolution(normalized, CapabilityState.LEARNING_REQUIRED, reason="capability is known but has no provider")
            authorized = tuple(provider for provider in providers if provider.authorized)
            if not authorized:
                return CapabilityResolution(normalized, CapabilityState.UNAUTHORIZED, providers=providers, reason="all providers are unauthorized")
            enabled = tuple(provider for provider in authorized if provider.enabled)
            if not enabled:
                return CapabilityResolution(normalized, CapabilityState.UNAVAILABLE, providers=authorized, reason="all authorized providers are unavailable")
            return CapabilityResolution(normalized, CapabilityState.RESOLVED, providers=enabled)

    def resolve_all(self, capabilities: Iterable[str]) -> tuple[CapabilityResolution, ...]:
        return tuple(self.resolve(capability) for capability in capabilities)
