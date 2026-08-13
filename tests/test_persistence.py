from aurelix_runtime.persistence import RuntimeStore


def test_jobs_survive_reopen(tmp_path):
    db = tmp_path / "runtime.db"
    store = RuntimeStore(db)
    job = store.enqueue("academy.research", {"topic": "agent security"})
    claimed = store.claim_next()
    assert claimed is not None
    assert claimed.job_id == job.job_id
    store.close()

    reopened = RuntimeStore(db)
    assert reopened.recover_running_jobs() == 1
    recovered = reopened.claim_next()
    assert recovered is not None
    assert recovered.job_id == job.job_id
    reopened.finish(recovered.job_id, True)
    reopened.close()


def test_recovery_does_not_loop_after_max_attempts(tmp_path):
    db = tmp_path / "runtime.db"
    store = RuntimeStore(db)
    job = store.enqueue("unstable", {})

    claimed = store.claim_next(max_attempts=2)
    assert claimed is not None
    store.finish(job.job_id, False, "first failure", retry=True)

    claimed = store.claim_next(max_attempts=2)
    assert claimed is not None
    assert claimed.attempts == 2

    store.close()

    reopened = RuntimeStore(db)
    assert reopened.recover_running_jobs(max_attempts=2) == 1
    assert reopened.status()["failed"] == 1
    assert reopened.claim_next(max_attempts=2) is None
    reopened.close()
