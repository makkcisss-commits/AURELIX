from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any

from aurelix_core.governor import Governor, GovernorRoute

from .job_queue import PersistentJobQueue, QueuedJob
from .runtime import AurelixRuntime


@dataclass(frozen=True)
class Capability:
    name: str
    handler: Callable[[dict], Any]
    read_only: bool = True


class Orchestrator:
    """Selects capabilities and submits work through the canonical durable runtime."""

    def __init__(self, queue: PersistentJobQueue | None = None, governor: Governor | None = None,
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
        """Route a capability through Governor, then place it in the durable runtime."""
        runtime_has_capability = self.runtime is not None and (
            capability in self.runtime.handlers or capability in self.runtime.claimed_handlers
        )
        if capability not in self._capabilities and not runtime_has_capability:
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
        job_id = f"orchestrator-{capability}-{id(payload)}"
        self.queue.enqueue(job_id, payload.get("objective", ""))
        return job_id

    def run_once(self) -> bool:
        if self.runtime is not None:
            return self.runtime.run_once()
        assert self.queue is not None
        queued = [job for job in self.queue.jobs.values() if job.status == "queued"]
        if not queued:
            return False
        job: QueuedJob = queued[0]
        self.queue.execute(job.job_id)
        return True
