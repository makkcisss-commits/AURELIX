from aurelix_runtime.persistence import RuntimeStore

def test_only_one_runtime_can_claim_a_job(tmp_path):
    db = tmp_path / "runtime.db"; first = RuntimeStore(db); second = RuntimeStore(db)
    try:
        job = first.enqueue("pipeline.run", {"objective": "concurrency"}); claimed = first.claim_next(worker_id="worker-1")
        assert claimed is not None and claimed.job_id == job.job_id and claimed.status == "running"; assert second.claim_next(worker_id="worker-2") is None
    finally: first.close(); second.close()

def test_recovery_preserves_attempt_budget_and_job_identity(tmp_path):
    db = tmp_path / "runtime.db"; store = RuntimeStore(db)
    try:
        job = store.enqueue("pipeline.run", {"objective": "recovery"}); claimed = store.claim_next(max_attempts=2, worker_id="worker-1")
        assert claimed is not None and claimed.job_id == job.job_id and claimed.attempts == 1
        assert store.recover_running_jobs(stale_after_seconds=0) == 1
        recovered = store.claim_next(max_attempts=2, worker_id="worker-2")
        assert recovered is not None and recovered.job_id == job.job_id and recovered.attempts == 2
    finally: store.close()
