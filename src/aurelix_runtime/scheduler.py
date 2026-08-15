from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from typing import Callable

from .job_queue import PersistentJobQueue
from .job_runner import AutonomyJobRunner


@dataclass(frozen=True)
class Schedule:
    name: str
    interval_seconds: float
    job_kind: str
    payload: dict[str, str]


@dataclass(frozen=True)
class SchedulerConfig:
    max_jobs_per_tick: int = 1
    max_attempts: int = 3


class Scheduler:
    """Scheduler feeding the canonical durable runtime without bypassing system governance."""

    APPROVED_JOB_KINDS = frozenset({"research_pipeline", "autonomy.run", "pipeline.run", "system.cycle"})

    def __init__(self, submit: Callable[[str, dict[str, str]], str] | None = None,
                 queue: PersistentJobQueue | None = None,
                 config: SchedulerConfig | None = None) -> None:
        self.config = config or SchedulerConfig()
        self.submit = submit or self._submit
        owner = getattr(submit, "__self__", None) if submit is not None else None
        self._runtime = getattr(owner, "runtime", owner) if owner is not None else None
        self.queue = queue or (PersistentJobQueue(store=self._runtime.store)
                               if self._runtime is not None and hasattr(self._runtime, "store")
                               else PersistentJobQueue())
        self._uses_default_submit = submit is None
        self.schedules: list[Schedule] = []
        self._stop = threading.Event()
        self._schedule_db = getattr(self.queue.store, "db", None)
        self._schedule_lock = getattr(self.queue.store, "lock", threading.RLock())
        self._ensure_schedule_store()
        self._load_schedules()

    def _ensure_schedule_store(self) -> None:
        if self._schedule_db is None:
            return
        with self._schedule_lock, self._schedule_db:
            self._schedule_db.execute("""
                CREATE TABLE IF NOT EXISTS schedules (
                    name TEXT PRIMARY KEY,
                    interval_seconds REAL NOT NULL,
                    job_kind TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

    def _load_schedules(self) -> None:
        if self._schedule_db is None:
            return
        with self._schedule_lock:
            rows = self._schedule_db.execute(
                "SELECT name, interval_seconds, job_kind, payload FROM schedules ORDER BY name"
            ).fetchall()
        self.schedules = [
            Schedule(row["name"], float(row["interval_seconds"]), row["job_kind"], json.loads(row["payload"]))
            for row in rows
        ]

    def _persist_schedule(self, schedule: Schedule) -> None:
        if self._schedule_db is None:
            return
        with self._schedule_lock, self._schedule_db:
            self._schedule_db.execute(
                """INSERT INTO schedules(name, interval_seconds, job_kind, payload, updated_at)
                   VALUES(?,?,?,?,?)
                   ON CONFLICT(name) DO UPDATE SET
                     interval_seconds=excluded.interval_seconds,
                     job_kind=excluded.job_kind,
                     payload=excluded.payload,
                     updated_at=excluded.updated_at""",
                (schedule.name, schedule.interval_seconds, schedule.job_kind,
                 json.dumps(schedule.payload, sort_keys=True), str(time.time_ns())),
            )

    def remove(self, name: str) -> bool:
        before = len(self.schedules)
        self.schedules = [schedule for schedule in self.schedules if schedule.name != name]
        removed = len(self.schedules) != before
        if self._schedule_db is not None:
            with self._schedule_lock, self._schedule_db:
                cursor = self._schedule_db.execute("DELETE FROM schedules WHERE name=?", (name,))
                removed = removed or cursor.rowcount == 1
        return removed

    def reload(self) -> None:
        """Reload durable schedule definitions after process restart or admin changes."""
        self._load_schedules()

    def _submit(self, job_kind: str, payload: dict[str, str]) -> str:
        if job_kind not in self.APPROVED_JOB_KINDS:
            raise PermissionError(f"job kind not approved: {job_kind}")
        job_id = f"scheduled-{job_kind}-{time.time_ns()}"
        self.queue.enqueue(job_id, payload.get("objective", ""))
        return job_id

    def add(self, schedule: Schedule) -> None:
        if schedule.interval_seconds < 1:
            raise ValueError("interval_seconds must be >= 1")
        if self._uses_default_submit and schedule.job_kind not in self.APPROVED_JOB_KINDS:
            raise PermissionError(f"job kind not approved: {schedule.job_kind}")
        # A schedule name is a durable identity, not a request to append another
        # copy. Re-registering it updates the canonical schedule in place.
        for index, existing in enumerate(self.schedules):
            if existing.name == schedule.name:
                self.schedules[index] = schedule
                self._persist_schedule(schedule)
                return
        self.schedules.append(schedule)
        self._persist_schedule(schedule)

    def tick(self) -> list[str]:
        processed: list[str] = []
        if self._runtime is not None and hasattr(self._runtime, "run_once"):
            for _ in range(self.config.max_jobs_per_tick):
                if not self._runtime.run_once():
                    break
                processed.append("runtime")
            return processed
        runner = AutonomyJobRunner(self.queue.store)
        for job in list(self.queue.jobs.values()):
            if len(processed) >= self.config.max_jobs_per_tick:
                break
            if job.status != "queued" or job.attempts >= self.config.max_attempts:
                continue
            self.queue.execute(job.job_id, runner)
            processed.append(job.job_id)
        return processed

    def recover(self) -> int:
        if self._runtime is not None and hasattr(self._runtime, "store"):
            recovered = self._runtime.store.recover_running_jobs(self.config.max_attempts)
            self.queue._refresh()
            return recovered
        return self.queue.recover_running()

    def serve_forever(self) -> None:
        next_run = {s.name: time.monotonic() for s in self.schedules}
        while not self._stop.is_set():
            now = time.monotonic()
            for schedule in self.schedules:
                if now >= next_run[schedule.name]:
                    self.submit(schedule.job_kind, schedule.payload)
                    next_run[schedule.name] = now + schedule.interval_seconds
            self.tick()
            self._stop.wait(0.5)

    def stop(self) -> None:
        self._stop.set()
