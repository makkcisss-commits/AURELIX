from pathlib import Path

from aurelix_runtime.persistence import RuntimeStore


def test_recovery_finalizes_running_job_with_durable_result(tmp_path: Path) -> None:
    store = RuntimeStore(tmp_path / "aurelix.db")
    job = store.enqueue("demo", {"value": 1})
    claimed = store.claim(job.job_id, worker_id="worker-1")
    assert claimed is not None

    store.record_result(job.job_id, {"ok": True, "value": 42})

    assert store.recover_running_jobs(max_attempts=3, stale_after_seconds=0) == 1
    recovered = store.get(job.job_id)
    assert recovered is not None
    assert recovered.status == "completed"
    assert recovered.attempts == 1
    assert store.get_result(job.job_id) == {"ok": True, "value": 42}

    # A second recovery is a no-op and cannot cause a retry.
    assert store.recover_running_jobs(max_attempts=3, stale_after_seconds=0) == 0


def test_recovery_requeues_running_job_without_durable_result(tmp_path: Path) -> None:
    store = RuntimeStore(tmp_path / "aurelix.db")
    job = store.enqueue("demo")
    claimed = store.claim(job.job_id, worker_id="worker-1")
    assert claimed is not None

    assert store.recover_running_jobs(max_attempts=3, stale_after_seconds=0) == 1
    recovered = store.get(job.job_id)
    assert recovered is not None
    assert recovered.status == "queued"
    assert store.get_result(job.job_id) is None
