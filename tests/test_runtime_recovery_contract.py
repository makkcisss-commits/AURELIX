from datetime import datetime, timedelta, timezone

from aurelix_runtime.persistence import RuntimeStore


def test_stale_running_job_is_requeued_without_success(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db")
    job = store.enqueue("demo", {"objective": "recover me"})
    claimed = store.claim(job.job_id, max_attempts=3, worker_id="dead-worker")
    assert claimed is not None

    stale = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    with store.lock, store.db:
        store.db.execute(
            "UPDATE jobs SET heartbeat_at=?, updated_at=? WHERE job_id=?",
            (stale, stale, job.job_id),
        )

    assert store.recover_running_jobs(max_attempts=3, stale_after_seconds=1) == 1
    recovered = store.get(job.job_id)
    assert recovered is not None
    assert recovered.status == "queued"
    assert store.get_result(job.job_id) is None

    retry = store.claim(job.job_id, max_attempts=3, worker_id="new-worker")
    assert retry is not None
    assert retry.attempts == 2
    store.finish(job.job_id, True, result={"ok": True})
    assert store.get(job.job_id).status == "completed"
    assert store.get_result(job.job_id) == {"ok": True}
    store.close()


def test_recovery_after_max_attempts_is_terminal_failure(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db")
    job = store.enqueue("demo", {})
    claimed = store.claim(job.job_id, max_attempts=1, worker_id="dead-worker")
    assert claimed is not None

    stale = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    with store.lock, store.db:
        store.db.execute(
            "UPDATE jobs SET heartbeat_at=? WHERE job_id=?",
            (stale, job.job_id),
        )

    assert store.recover_running_jobs(max_attempts=1, stale_after_seconds=1) == 1
    recovered = store.get(job.job_id)
    assert recovered is not None
    assert recovered.status == "failed"
    assert store.get_result(job.job_id) == {
        "ok": False,
        "error": "interrupted after maximum attempts",
    }
    store.close()
