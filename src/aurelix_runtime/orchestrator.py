from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any

from aurelix_core.governor import Governor, GovernorRoute

from .runtime import AurelixRuntime


@dataclass(frozen=True)
class Capability:
    name: str
    handler: Callable[[dict], Any]
    read_only: bool = True


class Orchestrator:
    """Coordinates work through the canonical durable runtime."""

    def __init__(self, queue: Any | None = None, governor: Governor | None = None,
                 runtime: AurelixRuntime | None = None) -> None:
        # The durable runtime is the canonical execution fabric. Keep the queue
        # argument only for API compatibility; direct queue execution is no
        # longer supported because it bypasses RuntimeStore leases, results,
        # and audit events.
        if runtime is None:
            raise ValueError("runtime is required; use AurelixRuntime as the canonical queue/worker fabric")
        self.runtime = runtime
        self.queue = queue
        self.governor = governor or Governor()
        self._capabilities: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        if capability.name in self._capabilities:
            raise ValueError(f"capability already registered: {capability.name}")
        self._capabilities[capability.name] = capability
        self.runtime.register(capability.name, capability.handler)

    def submit(self, *, capability: str, payload: dict, risk: int = 0,
               requires_capital: bool = False, production_change: bool = False) -> str:
        if capability not in self._capabilities:
            raise KeyError(f"unknown capability: {capability}")
        route = self.governor.route(
            source="orchestrator", action=capability,
            requires_capital=requires_capital, risk=risk,
            production_change=production_change,
        )
        if route.route is not GovernorRoute.POLICY_ALLOWED:
            raise PermissionError(route.reasons)
        return self.runtime.submit(capability, payload)

    def run_once(self) -> bool:
        return self.runtime.run_once()
