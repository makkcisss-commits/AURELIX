from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any

from aurelix_core.governor import Governor, GovernorRoute

from .scheduler import Job, JobQueue
from .runtime import AurelixRuntime


@dataclass(frozen=True)
class Capability:
    name: str
    handler: Callable[[dict], Any]
    read_only: bool = True


class Orchestrator:
    """Coordinates work through the canonical durable runtime when available."""

    def __init__(self, queue: JobQueue | None = None, governor: Governor | None = None,
                 runtime: AurelixRuntime | None = None) -> None:
        if queue is None and runtime is None:
            raise ValueError("queue or runtime is required")
        self.queue = queue
        self.runtime = runtime
        self.governor = governor or Governor()
        self._capabilities: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        if capability.name in self._capabilities:
            raise ValueError(f"capability already registered: {capability.name}")
        self._capabilities[capability.name] = capability
        if self.runtime is not None:
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
        if self.runtime is not None:
            return self.runtime.submit(capability, payload)
        assert self.queue is not None
        return self.queue.enqueue(Job(kind=capability, payload=payload))

    def run_once(self) -> bool:
        if self.runtime is not None:
            return self.runtime.run_once()
        assert self.queue is not None
        job = self.queue.claim()
        if job is None:
            return False
        capability = self._capabilities[job.kind]
        try:
            capability.handler(job.payload)
            self.queue.complete(job.job_id)
        except Exception as exc:
            self.queue.fail(job.job_id, str(exc))
        return True
