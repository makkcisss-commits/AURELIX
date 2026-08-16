"""Single-process AURELIX system boundary."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from aurelix_core.governor import Governor, GovernorRoute

from .message_fabric import AgentMessage, MessageFabric
from .mission_contracts import DEFAULT_ECONOMIC_TASKS, EconomicMission
from .runtime import AurelixRuntime, RuntimeConfig
from .schedule_registry import ScheduleRegistry
from .scheduler import Schedule, Scheduler, SchedulerConfig


@dataclass(frozen=True)
class SystemConfig:
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    scheduler: SchedulerConfig = field(default_factory=lambda: SchedulerConfig(max_jobs_per_tick=4, max_attempts=3))
    enable_autonomy: bool = True
    economic_cycle_seconds: float = 900.0
    economic_objective: str = "find and qualify verified revenue, business, and collaboration opportunities"


class AurelixSystem:
    """Canonical long-running facade over one EngineFactory composition."""

    def __init__(self, config: SystemConfig | None = None, *, runtime: AurelixRuntime | None = None,
                 cycle_handler: Callable[[str], Any] | None = None,
                 governor: Governor | None = None, factory=None) -> None:
        self.config = config or SystemConfig()
        if self.config.economic_cycle_seconds < 1:
            raise ValueError("economic_cycle_seconds must be >= 1")
        self.factory = factory
        self._standalone_cycle_fallback = False
        if factory is not None:
            self.runtime = factory.runtime
            self._owns_runtime = False
            self.governor = factory.governor
            self.fabric = factory.message_fabric
            self.cycle_handler = cycle_handler or factory.run_system_cycle
        else:
            self.runtime = runtime or AurelixRuntime(self.config.runtime)
            self._owns_runtime = runtime is None
            self.governor = governor or Governor()
            self.fabric = MessageFabric()
            self.cycle_handler = cycle_handler

        self.mission = EconomicMission(self.config.economic_objective, source="system")
        self.mission.plan(list(DEFAULT_ECONOMIC_TASKS))
        self.fabric.subscribe("governor.decision", self._record_governor_message)
        self.fabric.subscribe("mission.created", self._record_mission_message)
        if self.config.enable_autonomy and "autonomy.run" not in self.runtime.claimed_handlers:
            self.runtime.register_autonomy()

        # A standalone system has no EnterpriseLoop to execute a full economic
        # cycle. Keep the existing standalone autonomy behavior, while still
        # making an explicitly requested system-cycle schedule executable: it
        # delegates the objective to the already-registered durable autonomy job.
        if self.cycle_handler is None and self.config.enable_autonomy:
            self._standalone_cycle_fallback = True
            self.cycle_handler = lambda objective: self.runtime.submit("autonomy.run", {"objective": objective})

        if self.cycle_handler is not None:
            self.runtime.register("system.cycle", lambda payload: self.cycle_handler(str(payload.get("objective", ""))))

        self.scheduler = Scheduler(submit=self.submit, config=self.config.scheduler)
        self.schedule_registry = ScheduleRegistry(self.store)
        self._stop = threading.Event()
        self._started = False
        self._next_run: dict[str, float] = {}
        self._schedule_lock = threading.RLock()

        # Schedule definitions are durable configuration, not transient
        # process state. Existing schedules are restored before defaults are
        # registered; re-registering a name remains an idempotent update.
        for persisted in self.schedule_registry.load():
            self.scheduler.add(persisted)
            self._next_run.setdefault(persisted.name, time.monotonic())

        if self.config.enable_autonomy:
            if self.factory is not None and self.cycle_handler is not None:
                self.schedule_system_cycle("economic-discovery", self.config.economic_cycle_seconds, self.config.economic_objective)
            elif self._standalone_cycle_fallback:
                self.schedule_autonomy("economic-discovery", self.config.economic_cycle_seconds, self.config.economic_objective)
            elif self.cycle_handler is None:
                self.schedule_autonomy("economic-discovery", self.config.economic_cycle_seconds, self.config.economic_objective)

    @property
    def store(self):
        return self.runtime.store

    @property
    def status(self) -> str:
        return "stopping" if self._stop.is_set() else ("running" if self._started else "stopped")

    def _record_governor_message(self, message: AgentMessage) -> None:
        self.store.record_audit(None, "fabric.governor_decision", {
            "actor": message.sender, "subject": message.payload.get("action"),
            "outcome": message.payload.get("outcome"), "correlation_id": message.correlation_id,
        })

    def _record_mission_message(self, message: AgentMessage) -> None:
        self.store.record_audit(None, "fabric.mission_created", {
            "actor": message.sender, "subject": message.payload.get("mission_id"),
            "outcome": "created", "correlation_id": message.correlation_id,
        })

    def schedule_autonomy(self, name: str, interval_seconds: float, objective: str) -> None:
        self._schedule(name, interval_seconds, "autonomy.run", objective)

    def schedule_system_cycle(self, name: str, interval_seconds: float, objective: str) -> None:
        if self.cycle_handler is None:
            raise RuntimeError("system cycle handler is not configured")
        self._schedule(name, interval_seconds, "system.cycle", objective)

    def _schedule(self, name: str, interval_seconds: float, job_kind: str, objective: str) -> None:
        if not name.strip():
            raise ValueError("schedule name is required")
        if interval_seconds < 1:
            raise ValueError("interval_seconds must be >= 1")
        if not objective.strip():
            raise ValueError("objective is required")
        schedule = Schedule(name, interval_seconds, job_kind, {"objective": objective})
        with self._schedule_lock:
            self.scheduler.add(schedule)
            self.schedule_registry.save(schedule)
            self._next_run.setdefault(name, time.monotonic())

    def submit(self, kind: str, payload: dict[str, str] | None = None, *, risk: int = 0,
               requires_capital: bool = False, production_change: bool = False) -> str:
        """Submit work only after the canonical Governor routing decision."""
        route = self.governor.route(
            source="system",
            action=kind,
            requires_capital=requires_capital,
            risk=risk,
            production_change=production_change,
        )
        decision = AgentMessage(
            topic="governor.decision", sender="governor",
            payload={"action": kind, "outcome": route.route.value, "request_id": route.request_id},
            policy_context={"risk": risk, "requires_capital": requires_capital, "production_change": production_change},
        )
        self.fabric.publish(decision)
        if route.route is not GovernorRoute.POLICY_ALLOWED:
            self.store.record_audit(
                None,
                "system.submission_blocked",
                {"actor": "governor", "subject": kind, "outcome": route.route.value,
                 "request_id": route.request_id, "reasons": list(route.reasons)},
            )
            raise PermissionError(route.reasons)
        return self.runtime.submit(kind, payload or {})

    def _enqueue_due(self) -> int:
        now = time.monotonic()
        count = 0
        with self._schedule_lock:
            for schedule in self.scheduler.schedules:
                if now < self._next_run.get(schedule.name, now):
                    continue
                self.submit(schedule.job_kind, schedule.payload)
                self._next_run[schedule.name] = now + schedule.interval_seconds
                self.store.record_audit(
                    None,
                    "schedule.enqueued",
                    {"actor": "scheduler", "subject": schedule.name, "outcome": "queued", "job_kind": schedule.job_kind},
                )
                count += 1
        return count

    def tick(self) -> list[str]:
        if not self._started:
            raise RuntimeError("system is not started")
        self._enqueue_due()
        return self.scheduler.tick()

    def start(self) -> None:
        if self._started:
            return
        self.scheduler.recover()
        self._stop.clear()
        self._started = True
        self.fabric.publish(AgentMessage(
            topic="mission.created", sender="governor",
            recipient="orchestrator", payload={"mission_id": self.mission.mission_id, "objective": self.mission.objective},
            provenance={"tasks": [task.name for task in self.mission.tasks]},
        ))
        self.store.audit("system.started", "system", "system", "running", {"mission_id": self.mission.mission_id})

    def stop(self) -> None:
        if not self._started:
            return
        self._stop.set()
        self.scheduler.stop()
        self.runtime.stop()
        self._started = False
        self.store.audit("system.stopped", "system", "system", "stopped", {})

    def run_forever(self) -> None:
        self.start()
        try:
            while not self._stop.is_set():
                self.tick()
                self._stop.wait(self.config.runtime.worker_poll_seconds)
        finally:
            self.stop()

    def health(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "worker_id": self.runtime.worker_id,
            "store": "shared",
            "scheduler": "shared-runtime",
            "schedule_persistence": "durable-runtime-state",
            "governor": "canonical-submission-boundary",
            "fabric": "shared-composition-fabric" if self.factory is not None else "structured-topic-router",
            "composition": "engine-factory" if self.factory is not None else "standalone",
            "mission": {"id": self.mission.mission_id, "state": self.mission.state.value, "objective": self.mission.objective},
            "autonomy": "registered" if "autonomy.run" in self.runtime.claimed_handlers else "disabled",
            "system_cycle": "registered" if "system.cycle" in self.runtime.handlers else "disabled",
            "schedules": [s.name for s in self.scheduler.schedules],
        }

    def close(self) -> None:
        self.stop()
        if self._owns_runtime:
            self.runtime.close()
