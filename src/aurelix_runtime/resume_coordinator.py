"""Durable handoff from validated learning back into a fresh execution attempt."""
from __future__ import annotations

import json
from uuid import uuid4

from .persistence import RuntimeStore


class DurableResumeCoordinator:
    """Create one queued execution attempt per mission resume.

    The business mission identity is stable. Each resume gets a distinct
    execution identity, and the parent execution/result is never overwritten.
    """

    def __init__(self, store: RuntimeStore) -> None:
        self.store = store

    def resume(self, mission) -> str:
        execution_id = str(mission.execution_id).strip()
        mission_id = str(getattr(mission, "mission_id", "") or "").strip()
        if not execution_id or not mission_id:
            raise ValueError("mission resume requires execution_id and mission_id")
        key = f"mission-resume:{mission_id}"
        with self.store.lock:
            self.store.db.execute("BEGIN IMMEDIATE")
            try:
                parent = self.store.db.execute(
                    "SELECT status,name,payload FROM jobs WHERE job_id=?", (execution_id,)
                ).fetchone()
                if parent is None:
                    raise KeyError(f"execution not found: {execution_id}")
                if parent["status"] != "completed":
                    raise RuntimeError(f"execution {execution_id} cannot resume from state {parent['status']}")
                parent_result_row = self.store.db.execute(
                    "SELECT result FROM job_results WHERE job_id=?", (execution_id,)
                ).fetchone()
                if parent_result_row is None:
                    raise RuntimeError(f"execution {execution_id} has no durable result")
                parent_result = json.loads(parent_result_row[0])
                if parent_result.get("mission_id") != mission_id:
                    raise RuntimeError("mission identity does not match the durable parent execution")
                if parent_result.get("status") not in {"capability_learning_required", "capability_escalation_unavailable", "blocked", "awaiting_provider", "awaiting_validation"}:
                    raise RuntimeError("only a blocked mission execution can be resumed")

                existing_row = self.store.db.execute(
                    "SELECT value FROM runtime_state WHERE key=?", (key,)
                ).fetchone()
                if existing_row is not None:
                    state = json.loads(existing_row[0])
                    existing_id = str(state.get("execution_id") or "").strip()
                    if existing_id:
                        existing_job = self.store.db.execute(
                            "SELECT status FROM jobs WHERE job_id=?", (existing_id,)
                        ).fetchone()
                        if existing_job is not None and existing_job["status"] in {"queued", "running", "completed"}:
                            self.store.db.commit()
                            return existing_id

                child_id = f"{mission_id}:resume:{uuid4()}"
                payload = json.loads(parent["payload"])
                payload.update({"mission_id": mission_id, "parent_execution_id": execution_id})
                now = self.store._now()
                self.store.db.execute(
                    "INSERT INTO jobs(job_id,name,payload,status,attempts,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                    (child_id, parent["name"], json.dumps(payload, sort_keys=True), "queued", 0, now, now),
                )
                self.store.db.execute(
                    "INSERT INTO runtime_state(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (key, json.dumps({"state": "queued", "mission_id": mission_id, "blocked_execution_id": execution_id, "execution_id": child_id}, sort_keys=True)),
                )
                self.store.db.execute(
                    "INSERT INTO audit_events(event_id,job_id,event_type,payload,created_at) VALUES(?,?,?,?,?)",
                    (str(uuid4()), child_id, "runtime.execution_resumed", json.dumps({"mission_id": mission_id, "execution_id": child_id, "parent_execution_id": execution_id}, sort_keys=True), now),
                )
                self.store.db.commit()
                return child_id
            except Exception:
                self.store.db.rollback()
                raise
