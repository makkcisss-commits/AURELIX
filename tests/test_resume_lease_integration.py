import json
from pathlib import Path

import pytest

from aurelix_runtime.autonomy_fabric import AutonomyFabric
from aurelix_runtime.persistence import RuntimeStore


def _resume_state(store: RuntimeStore, blocked_execution_id: str) -> dict:
    with store.lock:
        row = store.db.execute(
            "SELECT value FROM runtime_state WHERE key=?",
            (f"mission-resume:{blocked_execution_id}",),
        ).fetchone()
    assert row is not None
    return json.loads(row[0])


def test_running_resume_reservation_tracks_active_runtime_lease(tmp_path: Path) -> None:
    store = RuntimeStore(tmp_path / "resume.db", lease_seconds=5)
    fabric = AutonomyFabric(store=store)
    blocked = "blocked-active"
    execution_id = fabric._claim_resume_execution(blocked)

    job = store.enqueue(
        "autonomy.run",
        {"objective": "resume test", "required_capabilities": []},
        execution_id=execution_id,
    )
    claimed = store.claim(job.job_id, worker_id="resume-worker")
    assert claimed is not None

    fabric._mark_resume_running(blocked, claimed)
    state = _resume_state(store, blocked)

    assert state["state"] == "running"
    assert state["execution_id"] == claimed.job_id
    assert state["worker_id"] == claimed.worker_id
    assert state["lease_token"] == claimed.lease_token
    assert state["lease_until"] == claimed.lease_until

    with pytest.raises(RuntimeError, match="already in progress"):
        fabric._claim_resume_execution(blocked)

    fabric.close()


def test_expired_reservation_gets_a_new_execution_id(tmp_path: Path) -> None:
    store = RuntimeStore(tmp_path / "resume.db", lease_seconds=5)
    fabric = AutonomyFabric(store=store)
    blocked = "blocked-expired"
    old_execution_id = "old-resume"
    with store.lock, store.db:
        store.db.execute(
            "INSERT INTO runtime_state(key,value) VALUES(?,?)",
            (f"mission-resume:{blocked}", json.dumps({"state": "reserved", "execution_id": old_execution_id, "lease_until": 0})),
        )

    new_execution_id = fabric._claim_resume_execution(blocked)

    assert new_execution_id != old_execution_id
    assert _resume_state(store, blocked)["execution_id"] == new_execution_id
    fabric.close()
