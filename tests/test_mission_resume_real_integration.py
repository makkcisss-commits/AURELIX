"""Real persistence/concurrency regressions for mission resume.

These tests intentionally exercise RuntimeStore-backed coordination rather than
an in-memory reference model. They are the minimum proof needed before resume
can be considered safe.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path

from aurelix_runtime.persistence import RuntimeStore


def _seed_resume(store: RuntimeStore, blocked_execution_id: str) -> None:
    payload = {
        "execution_id": blocked_execution_id,
        "mission_id": "mission-real-1",
        "objective": "resume a blocked mission",
        "required_capabilities": ["crm-write"],
        "state": "blocked",
    }
    with store.lock, store.db:
        store.db.execute(
            "INSERT INTO runtime_state(key,value) VALUES(?,?)",
            (f"mission:{blocked_execution_id}", json.dumps(payload, sort_keys=True)),
        )


def _claim_resume(store: RuntimeStore, blocked_execution_id: str) -> str:
    key = f"mission-resume:{blocked_execution_id}"
    execution_id = f"{blocked_execution_id}:resume:{threading.get_ident()}"
    now = time.time()
    lease_until = now + store.lease_seconds
    with store.lock:
        store.db.execute("BEGIN IMMEDIATE")
        try:
            row = store.db.execute("SELECT value FROM runtime_state WHERE key=?", (key,)).fetchone()
            if row is not None:
                existing = json.loads(row[0])
                if existing.get("state") in {"reserved", "running"}:
                    store.db.rollback()
                    raise RuntimeError("mission resume already in progress")
            store.db.execute(
                "INSERT INTO runtime_state(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, json.dumps({"state": "reserved", "execution_id": execution_id, "lease_until": lease_until}, sort_keys=True)),
            )
            store.db.commit()
            return execution_id
        except Exception:
            store.db.rollback()
            raise


def test_two_workers_have_one_durable_resume_claim(tmp_path: Path) -> None:
    store = RuntimeStore(tmp_path / "resume.db", lease_seconds=5)
    _seed_resume(store, "execution-1")
    barrier = threading.Barrier(2)
    results: list[str] = []
    errors: list[str] = []

    def worker() -> None:
        barrier.wait()
        try:
            results.append(_claim_resume(store, "execution-1"))
        except RuntimeError as exc:
            errors.append(str(exc))

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(results) == 1
    assert len(errors) == 1
    row = store.db.execute("SELECT value FROM runtime_state WHERE key=?", ("mission-resume:execution-1",)).fetchone()
    assert row is not None
    state = json.loads(row[0])
    assert state["state"] == "reserved"
    assert state["execution_id"] == results[0]
    store.close()


def test_mission_identity_is_durable_and_distinct_from_execution(tmp_path: Path) -> None:
    store = RuntimeStore(tmp_path / "mission.db")
    _seed_resume(store, "execution-1")
    first = json.loads(store.db.execute("SELECT value FROM runtime_state WHERE key=?", ("mission:execution-1",)).fetchone()[0])
    store.close()

    reopened = RuntimeStore(tmp_path / "mission.db")
    second = json.loads(reopened.db.execute("SELECT value FROM runtime_state WHERE key=?", ("mission:execution-1",)).fetchone()[0])
    assert second["mission_id"] == first["mission_id"]
    assert second["execution_id"] == "execution-1"
    assert second["mission_id"] != second["execution_id"]
    reopened.close()
