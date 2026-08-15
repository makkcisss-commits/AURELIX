import json
import time
from pathlib import Path

import pytest

from aurelix_runtime.autonomy_fabric import AutonomyFabric
from aurelix_runtime.persistence import RuntimeStore


def _put_resume_state(store: RuntimeStore, blocked_execution_id: str, value: dict) -> None:
    with store.lock, store.db:
        store.db.execute(
            "INSERT INTO runtime_state(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (f"mission-resume:{blocked_execution_id}", json.dumps(value, sort_keys=True)),
        )


def _get_resume_state(store: RuntimeStore, blocked_execution_id: str) -> dict:
    with store.lock:
        row = store.db.execute(
            "SELECT value FROM runtime_state WHERE key=?",
            (f"mission-resume:{blocked_execution_id}",),
        ).fetchone()
    return json.loads(row[0])


def test_expired_reserved_resume_can_be_reclaimed(tmp_path: Path) -> None:
    store = RuntimeStore(tmp_path / "resume.db", lease_seconds=5)
    fabric = AutonomyFabric(store=store)
    blocked = "blocked-1"
    _put_resume_state(store, blocked, {"state": "reserved", "execution_id": "old-resume", "lease_until": time.time() - 1})

    resumed = fabric._claim_resume_execution(blocked)

    assert resumed != "old-resume"
    state = _get_resume_state(store, blocked)
    assert state["state"] == "reserved"
    assert state["execution_id"] == resumed
    assert state["lease_until"] > time.time()
    fabric.close()


def test_active_reserved_resume_is_still_single_owner(tmp_path: Path) -> None:
    store = RuntimeStore(tmp_path / "resume.db", lease_seconds=5)
    fabric = AutonomyFabric(store=store)
    blocked = "blocked-2"
    _put_resume_state(store, blocked, {"state": "reserved", "execution_id": "active-resume", "lease_until": time.time() + 60})

    with pytest.raises(RuntimeError, match="already in progress"):
        fabric._claim_resume_execution(blocked)

    assert _get_resume_state(store, blocked)["execution_id"] == "active-resume"
    fabric.close()


def test_running_resume_is_reclaimable_when_runtime_execution_is_missing(tmp_path: Path) -> None:
    store = RuntimeStore(tmp_path / "resume.db", lease_seconds=5)
    fabric = AutonomyFabric(store=store)
    blocked = "blocked-3"
    _put_resume_state(store, blocked, {"state": "running", "execution_id": "crashed-resume"})

    resumed = fabric._claim_resume_execution(blocked)

    assert resumed != "crashed-resume"
    assert _get_resume_state(store, blocked)["execution_id"] == resumed
    fabric.close()
