from datetime import datetime, timedelta, timezone

from aurelix_runtime.runtime import RuntimeStore


def test_only_one_worker_can_claim_a_queued_job(tmp_path):
    store = RuntimeStore(str(tmp_path / "runtime.db"))
    job_id = store.enqueue("unit", {"value": "x"})
    first = store.claim("worker-a", lease_seconds=60)
    second = store.claim("worker-b", lease_seconds=60)
    assert first is not None
    assert first.job_id == job_id
    assert second is None


def test_live_lease_is_not_recovered(tmp_path):
    store = RuntimeStore(str(tmp_path / "runtime.db"))
    store.enqueue("unit", {})
    assert store.claim("worker-a", lease_seconds=60) is not None
    assert store.recover_running() == 0
    assert store.claim("worker-b", lease_seconds=60) is None


def test_expired_lease_is_recoverable_once(tmp_path):
    store = RuntimeStore(str(tmp_path / "runtime.db"))
    job_id = store.enqueue("unit", {})
    assert store.claim("worker-a", lease_seconds=60) is not None
    expired = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    with store.lock, store.db:
        store.db.execute("UPDATE jobs SET lease_until=? WHERE job_id=?", (expired, job_id))
    assert store.recover_running() == 1
    recovered = store.claim("worker-b", lease_seconds=60)
    assert recovered is not None
    assert recovered.job_id == job_id
    assert store.claim("worker-c", lease_seconds=60) is None


def test_old_worker_cannot_finish_after_lease_recovery(tmp_path):
    store = RuntimeStore(str(tmp_path / "runtime.db"))
    job_id = store.enqueue("unit", {})
    assert store.claim("worker-a", lease_seconds=60) is not None
    expired = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    with store.lock, store.db:
        store.db.execute("UPDATE jobs SET lease_until=? WHERE job_id=?", (expired, job_id))
    assert store.recover_running() == 1
    assert store.claim("worker-b", lease_seconds=60) is not None
    store.finish(job_id, "worker-a", True)
    status = store.status()
    assert status["running"] == 1
    assert status["succeeded"] == 0
    store.finish(job_id, "worker-b", True)
    status = store.status()
    assert status["running"] == 0
    assert status["succeeded"] == 1
