from aurelix_runtime.persistence import RuntimeStore


def test_jobs_survive_reopen(tmp_path):
    db = tmp_path / "runtime.db"
    store = RuntimeStore(db)
    job = store.enqueue("academy.research", {"topic": "agent security"})
    claimed = store.claim_next(worker_id="worker-1")
    assert claimed is not None and claimed.job_id == job.job_id
    store.close()

    reopened = RuntimeStore(db)
    assert reopened.recover_running_jobs(stale_after_seconds=0) == 1
    recovered = reopened.claim_next(worker_id="worker-2")
    assert recovered is not None and recovered.job_id == job.job_id
    reopened.finish(recovered.job_id, True, worker_id=recovered.worker_id, lease_token=recovered.lease_token)
    reopened.close()


def test_recovery_does_not_loop_after_max_attempts(tmp_path):
    db = tmp_path / "runtime.db"
    store = RuntimeStore(db)
    job = store.enqueue("unstable", {})
    claimed = store.claim_next(max_attempts=2, worker_id="worker-1")
    assert claimed is not None
    store.finish(job.job_id, False, "first failure", retry=True, worker_id=claimed.worker_id, lease_token=claimed.lease_token)
    claimed = store.claim_next(max_attempts=2, worker_id="worker-1")
    assert claimed is not None and claimed.attempts == 2
    store.close()
    reopened = RuntimeStore(db)
    assert reopened.recover_running_jobs(max_attempts=2, stale_after_seconds=0) == 1
    assert reopened.status()["failed"] == 1
    assert reopened.claim_next(max_attempts=2, worker_id="worker-2") is None
    reopened.close()
