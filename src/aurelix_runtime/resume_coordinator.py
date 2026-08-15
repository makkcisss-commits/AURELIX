"""Durable handoff from validated learning back into a new execution attempt."""
from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from .persistence import RuntimeStore


class DurableResumeCoordinator:
    """Create exactly one durable execution attempt for a validated mission resume.

    Mission identity is stable; execution identity is per attempt. The previous
    execution and its result are never deleted or reset. Concurrent resume calls
    for the same mission converge on the same queued attempt.
    """

    def __init__(self, store: RuntimeStore) -> None:
        self.store = store

    def resume(self, mission: Any) -> str:
        blocked_execution_id = str(mission.execution_id).strip()
        mission_id = str(getattr(mission, "mission_id", "") or blocked_execution_id).strip()
        if not blocked_execution_id:
            raise ValueError("validated mission must have an execution_id")
        if not mission_id:
            raise ValueError("validated mission must have a mission_id")

        resume_key = f"mission-resume:{mission_id}"
        with self.store.lock:
            self.store.db.execute("BEGIN IMMEDIATE")
            try:
                row = self.store.db.execute(
                    "SELECT status, name, payload FROM jobs WHERE job_id=?",
                    (blocked_execution_id,),
                ).fetchone()
                if row is None:
                    raise KeyError(f"execution not found: {blocked_execution_id}")
                if row["status"] not in {"completed", "queued"}:
                    raise RuntimeError(
                        f"execution {blocked_execution_id} cannot resume from state {row['status']}"
                    )

                state_row = self.store.db.execute(
                    "SELECT value FROM runtime_state WHERE key=?",
                    (resume_key,),
                ).fetchone()
                if state_row is not None:
                    state = json.loads(state_row[0])
                    existing_execution = str(state.get("execution_id") or "").strip()
                    if existing_execution:
                        existing = self.store.db.execute(
                            "SELECT status FROM jobs WHERE job_id=?", (existing_execution,)
                        ).fetchone()
                        if existing is not None:
                            self.store.db.commit()
                            return existing_execution

                new_execution_id = f"{mission_id}:resume:{uuid4()}"
                payload = json.loads(row["payload"])
                payload["mission_id"] = mission_id
                now = self.store._now()
                self.store.db.execute(
                    """INSERT INTO jobs(
                        job_id,name,payload,status,attempts,created_at,updated_at
                    ) VALUES(?,?,?,?,?,?,?)""",
                    (
                        new_execution_id,
                        row["name"],
                        json.dumps(payload, sort_keys=True),
                        "queued",
                        0,
                        now,
                        now,
                    ),
                )
                self.store.db.execute(
                    """INSERT INTO runtime_state(key,value) VALUES(?,?)
                       ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
                    (
                        resume_key,
                        json.dumps({
                            "state": "queued",
                            "mission_id": mission_id,
                            "blocked_execution_id": blocked_execution_id,
                            "execution_id": new_execution_id,
                        }, sort_keys=True),
                    ),
                )
                self.store.db.execute(
                    "INSERT INTO audit_events(event_id,job_id,event_type,payload,created_at) VALUES(?,?,?,?,?)",
                    (
                        str(uuid4()),
                        new_execution_id,
                        "runtime.execution_resumed",
                        json.dumps({
                            "reason": "validated_capability",
                            "mission_id": mission_id,
                            "execution_id": new_execution_id,
                            "parent_execution_id": blocked_execution_id,
                            "same_execution": False,
                        }, sort_keys=True),
                        now,
                    ),
                )
                self.store.db.commit()
                return new_execution_id
            except Exception:
                self.store.db.rollback()
                raise
