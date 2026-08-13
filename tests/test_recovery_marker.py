from datetime import datetime, timedelta, timezone

from aurelix_runtime.persistence import RuntimeStore


def test_recovery_completes_running_job_with_durable_result(tmp_path):
    store = RuntimeStore(tmp_path / "aurelix.db")
    job = store.enqueue("demo", {"value": 1})
    assert store.claim(job.job_id, worker_id="worker-a") is not None
    store.record_result(job.job_id, {"ok": True, "value": 42})
    stale = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
    with store.lock, store.db:
        store.db.execute("UPDATE jobs SET heartbeat_at=? WHERE job_id=?", (stale, job.job_id))
    assert store.recover_running_jobs(stale_after_seconds=1) == 1
    assert store.get(job.job_id).status == "completed"
    assert store.get_result(job.job_id) == {"ok": True, "value": 42}
    store.close()
