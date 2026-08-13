from aurelix_runtime.persistence import RuntimeStore


def test_running_job_recovers_once_after_restart(tmp_path):
    db = tmp_path / "runtime.db"
    first = RuntimeStore(db)
    job = first.enqueue("demo", {"value": "1"})
    claimed = first.claim_next()
    assert claimed is not None
    assert claimed.job_id == job.job_id
    assert claimed.attempts == 1
    first.close()

    second = RuntimeStore(db)
    assert second.recover_running_jobs() == 1
    recovered = second.claim_next()
    assert recovered is not None
    assert recovered.job_id == job.job_id
    assert recovered.attempts == 2

    second.finish(recovered.job_id, True)
    with second.lock:
        row = second.db.execute(
            "SELECT status, attempts FROM jobs WHERE job_id=?", (job.job_id,)
        ).fetchone()
        result = second.db.execute(
            "SELECT result FROM job_results WHERE job_id=?", (job.job_id,)
        ).fetchone()
    assert row["status"] == "completed"
    assert row["attempts"] == 2
    assert result is not None
    second.close()


def test_finished_job_cannot_be_finished_twice(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db")
    job = store.enqueue("demo", {})
    claimed = store.claim_next()
    assert claimed is not None
    store.finish(job.job_id, True)

    try:
        store.finish(job.job_id, True)
    except RuntimeError as exc:
        assert "cannot finish" in str(exc)
    else:
        raise AssertionError("a completed job must not be finished twice")
    store.close()
