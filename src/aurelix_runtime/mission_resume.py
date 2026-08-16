"""Durable mission identity and exactly-once resume coordination."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(frozen=True)
class MissionState:
    mission_id: str
    objective: str
    required_capabilities: tuple[str, ...]
    status: str
    active_execution_id: str | None
    resume_state: str | None
    updated_at: str


class MissionResumeCoordinator:
    """Durable mission identity and atomic resume reservation boundary."""

    def __init__(self, store) -> None:
        self.store = store
        with self.store.lock, self.store.db:
            self.store.db.execute("""CREATE TABLE IF NOT EXISTS mission_state (
                mission_id TEXT PRIMARY KEY,
                objective TEXT NOT NULL,
                required_capabilities TEXT NOT NULL,
                status TEXT NOT NULL,
                active_execution_id TEXT,
                resume_state TEXT,
                updated_at TEXT NOT NULL
            )""")
            self.store.db.execute("CREATE INDEX IF NOT EXISTS idx_mission_state_active ON mission_state(active_execution_id)")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _record(row) -> MissionState:
        return MissionState(
            row["mission_id"], row["objective"], tuple(json.loads(row["required_capabilities"])),
            row["status"], row["active_execution_id"], row["resume_state"], row["updated_at"],
        )

    def register(self, *, mission_id: str, objective: str, required_capabilities: list[str]) -> MissionState:
        if not mission_id.strip() or not objective.strip():
            raise ValueError("mission_id and objective are required")
        capabilities = tuple(dict.fromkeys(c.strip() for c in required_capabilities if c.strip()))
        now = self._now()
        with self.store.lock:
            self.store.db.execute("BEGIN IMMEDIATE")
            try:
                row = self.store.db.execute("SELECT * FROM mission_state WHERE mission_id=?", (mission_id,)).fetchone()
                if row:
                    if row["objective"] != objective or tuple(json.loads(row["required_capabilities"])) != capabilities:
                        raise ValueError("mission identity is already bound to another contract")
                    self.store.db.commit()
                    return self._record(row)
                self.store.db.execute(
                    "INSERT INTO mission_state VALUES(?,?,?,?,?,?,?)",
                    (mission_id, objective, json.dumps(capabilities), "active", None, None, now),
                )
                self.store.db.commit()
                return self.get(mission_id)
            except Exception:
                self.store.db.rollback()
                raise

    def block(self, *, mission_id: str, execution_id: str, reason: str) -> MissionState:
        now = self._now()
        with self.store.lock, self.store.db:
            cursor = self.store.db.execute(
                "UPDATE mission_state SET status='blocked', active_execution_id=?, resume_state=?, updated_at=? WHERE mission_id=?",
                (execution_id, reason, now, mission_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(mission_id)
            row = self.store.db.execute("SELECT * FROM mission_state WHERE mission_id=?", (mission_id,)).fetchone()
        return self._record(row)

    def reserve_resume(self, *, mission_id: str, execution_id: str) -> bool:
        now = self._now()
        with self.store.lock:
            self.store.db.execute("BEGIN IMMEDIATE")
            try:
                row = self.store.db.execute(
                    "SELECT status, active_execution_id, objective, required_capabilities FROM mission_state WHERE mission_id=?",
                    (mission_id,),
                ).fetchone()
                if row is None or row["status"] != "blocked":
                    self.store.db.rollback()
                    if row is None:
                        raise KeyError(mission_id)
                    return False
                existing_id = row["active_execution_id"]
                if existing_id and existing_id != execution_id:
                    existing = self.store.db.execute("SELECT status FROM jobs WHERE job_id=?", (existing_id,)).fetchone()
                    if existing and existing["status"] in {"queued", "running"}:
                        self.store.db.rollback()
                        return False
                payload = {"objective": row["objective"], "mission_id": mission_id,
                           "required_capabilities": json.loads(row["required_capabilities"])}
                self.store.db.execute(
                    "INSERT INTO jobs(job_id,name,payload,status,attempts,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                    (execution_id, "autonomy.run", json.dumps(payload, sort_keys=True), "queued", 0, now, now),
                )
                cursor = self.store.db.execute(
                    "UPDATE mission_state SET status='resume_reserved', active_execution_id=?, updated_at=? WHERE mission_id=? AND status='blocked'",
                    (execution_id, now, mission_id),
                )
                if cursor.rowcount != 1:
                    self.store.db.rollback()
                    return False
                self.store.db.commit()
                return True
            except Exception:
                self.store.db.rollback()
                raise

    def release_resume(self, *, mission_id: str, execution_id: str, parent_execution_id: str | None) -> MissionState:
        """Fail an unclaimed resume without deleting its durable execution evidence."""
        now = self._now()
        with self.store.lock:
            self.store.db.execute("BEGIN IMMEDIATE")
            try:
                row = self.store.db.execute("SELECT status, active_execution_id FROM mission_state WHERE mission_id=?", (mission_id,)).fetchone()
                if row is None:
                    raise KeyError(mission_id)
                if row["status"] == "resume_reserved" and row["active_execution_id"] == execution_id:
                    self.store.db.execute(
                        "UPDATE jobs SET status='failed', updated_at=? WHERE job_id=? AND status='queued'",
                        (now, execution_id),
                    )
                    self.store.db.execute(
                        "UPDATE mission_state SET status='blocked', active_execution_id=NULL, resume_state='resume_claim_unavailable', updated_at=? WHERE mission_id=? AND status='resume_reserved' AND active_execution_id=?",
                        (now, mission_id, execution_id),
                    )
                self.store.db.commit()
                return self.get(mission_id)
            except Exception:
                self.store.db.rollback()
                raise

    def activate(self, *, mission_id: str, execution_id: str) -> MissionState:
        now = self._now()
        with self.store.lock, self.store.db:
            cursor = self.store.db.execute(
                "UPDATE mission_state SET status='active', active_execution_id=?, resume_state=NULL, updated_at=? WHERE mission_id=? AND active_execution_id=?",
                (execution_id, now, mission_id, execution_id),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("mission activation fenced: execution is no longer authoritative")
            row = self.store.db.execute("SELECT * FROM mission_state WHERE mission_id=?", (mission_id,)).fetchone()
        return self._record(row)

    def get(self, mission_id: str) -> MissionState | None:
        with self.store.lock:
            row = self.store.db.execute("SELECT * FROM mission_state WHERE mission_id=?", (mission_id,)).fetchone()
        return self._record(row) if row else None

    @staticmethod
    def new_execution_id() -> str:
        return str(uuid4())
