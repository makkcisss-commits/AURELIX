from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from aurelix_core.governor import Governor, GovernorRoute

from .scheduler import Job, JobQueue


@dataclass(frozen=True)
class Capability:
    name: str
    handler: Callable[[dict], None]
    read_only: bool = True


class Orchestrator:
    """Coordinates autonomous work while keeping execution behind Governor policy."""

    def __init__(self, queue: JobQueue, governor: Governor) -> None:
        self.queue = queue
        self.governor = governor
        self._capabilities: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        if capability.name in self._capabilities:
            raise ValueError(f"capability already registered: {capability.name}")
        self._capabilities[capability.name] = capability

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
        return self.queue.enqueue(Job(kind=capability, payload=payload))

    def run_once(self) -> bool:
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
