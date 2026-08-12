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
    reopened.finish(recovered.job_id, {"ok": True})
    reopened.close()
