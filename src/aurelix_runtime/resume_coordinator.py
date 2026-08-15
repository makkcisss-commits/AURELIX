"""Durable handoff from validated learning back into the same runtime execution."""
from __future__ import annotations

from typing import Any

from .persistence import RuntimeStore


class DurableResumeCoordinator:
    """Re-queue the existing execution id after validated learning.

    This deliberately reopens the same durable job instead of creating a new
    execution. The Runtime remains the execution authority; this coordinator
    only performs the atomic state transition from completed learning back to
    queued work after the Governor/AdaptiveLoop has declared the mission ready.
    """

    def __init__(self, store: RuntimeStore) -> None:
        self.store = store

    def resume(self, mission: Any) -> str:
        execution_id = str(mission.execution_id).strip()
        if not execution_id:
            raise ValueError("validated mission must have an execution_id")

        with self.store.lock, self.store.db:
            row = self.store.db.execute(
                "SELECT status, name, payload FROM jobs WHERE job_id=?",
                (execution_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"execution not found: {execution_id}")
            if row["status"] == "queued":
                return execution_id
            if row["status"] != "completed":
                raise RuntimeError(
                    f"execution {execution_id} cannot resume from state {row['status']}"
                )

            self.store.db.execute(
                "DELETE FROM job_results WHERE job_id=?",
                (execution_id,),
            )
            self.store.db.execute(
                """UPDATE jobs
                   SET status='queued', attempts=0, updated_at=?,
                       worker_id=NULL, lease_token=NULL, lease_until=NULL,
                       heartbeat_at=NULL, last_error=NULL
                   WHERE job_id=? AND status='completed'""",
                (self.store._now(), execution_id),
            )
            self.store.record_audit(
                execution_id,
                "runtime.execution_resumed",
                {
                    "reason": "validated_capability",
                    "execution_id": execution_id,
                    "same_execution": True,
                },
            )
        return execution_id
