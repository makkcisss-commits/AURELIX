"""Durable persistence for scheduler definitions.

The existing Scheduler remains the execution mechanism. This registry only
persists schedule definitions so a Runtime restart does not silently erase the
autonomous loop configuration.
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .persistence import RuntimeStore
    from .scheduler import Schedule


class ScheduleRegistry:
    """Persist schedule definitions in the RuntimeStore runtime_state table."""

    PREFIX = "schedule:"

    def __init__(self, store: "RuntimeStore") -> None:
        self.store = store

    def save(self, schedule: "Schedule") -> None:
        value = json.dumps(
            {
                "name": schedule.name,
                "interval_seconds": schedule.interval_seconds,
                "job_kind": schedule.job_kind,
                "payload": schedule.payload,
            },
            sort_keys=True,
        )
        with self.store.lock, self.store.db:
            self.store.db.execute(
                "INSERT INTO runtime_state(key,value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (self.PREFIX + schedule.name, value),
            )

    def load(self) -> list["Schedule"]:
        from .scheduler import Schedule

        with self.store.lock:
            rows = self.store.db.execute(
                "SELECT key,value FROM runtime_state WHERE key LIKE ? ORDER BY key",
                (self.PREFIX + "%",),
            ).fetchall()

        schedules: list[Schedule] = []
        for row in rows:
            try:
                data = json.loads(row["value"])
                schedule = Schedule(
                    str(data["name"]),
                    float(data["interval_seconds"]),
                    str(data["job_kind"]),
                    {str(k): str(v) for k, v in dict(data.get("payload", {})).items()},
                )
                if schedule.name.strip() and schedule.interval_seconds >= 1 and schedule.job_kind.strip():
                    schedules.append(schedule)
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                # A corrupt optional schedule must never prevent the durable
                # Runtime from starting. It is intentionally left persisted so
                # diagnostics can identify the bad record later.
                continue
        return schedules
