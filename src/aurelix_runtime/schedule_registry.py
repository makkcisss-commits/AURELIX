"""Durable persistence for canonical AURELIX schedule definitions."""
from __future__ import annotations

import json
import time
from .persistence import RuntimeStore
from .scheduler import Schedule


class ScheduleRegistry:
    PREFIX = "schedule:"

    def __init__(self, store: RuntimeStore) -> None:
        self.store = store

    def save(self, schedule: Schedule, next_run_at: float | None = None) -> None:
        value = json.dumps({
            "name": schedule.name,
            "interval_seconds": schedule.interval_seconds,
            "job_kind": schedule.job_kind,
            "payload": schedule.payload,
            "next_run_at": next_run_at if next_run_at is not None else time.time(),
        }, sort_keys=True)
        with self.store.lock, self.store.db:
            self.store.db.execute(
                "INSERT INTO runtime_state(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (self.PREFIX + schedule.name, value),
            )

    def load(self) -> list[tuple[Schedule, float]]:
        with self.store.lock:
            rows = self.store.db.execute(
                "SELECT key,value FROM runtime_state WHERE key LIKE ? ORDER BY key",
                (self.PREFIX + "%",),
            ).fetchall()
        loaded: list[tuple[Schedule, float]] = []
        for row in rows:
            try:
                data = json.loads(row["value"])
                schedule = Schedule(
                    str(data["name"]),
                    float(data["interval_seconds"]),
                    str(data["job_kind"]),
                    {str(k): str(v) for k, v in dict(data.get("payload", {})).items()},
                )
                next_run_at = float(data["next_run_at"])
                if not schedule.name.strip() or schedule.interval_seconds < 1 or not schedule.job_kind.strip():
                    raise ValueError("invalid persisted schedule")
                loaded.append((schedule, next_run_at))
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                raise RuntimeError(f"invalid persisted schedule state: {row['key']}") from None
        return loaded

    def remove(self, name: str) -> bool:
        with self.store.lock, self.store.db:
            cursor = self.store.db.execute("DELETE FROM runtime_state WHERE key=?", (self.PREFIX + name,))
        return cursor.rowcount == 1
