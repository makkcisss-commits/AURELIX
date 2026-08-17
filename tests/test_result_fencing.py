import pytest

from aurelix_runtime.persistence import LeaseLostError, RuntimeStore


def test_stale_worker_cannot_persist_checkpoint_after_recovery(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db", lease_seconds=30)
    job = store.enqueue("demo", {})
    stale = store.claim(job.job_id, worker_id="worker-a")
    assert stale is not None

    with store.lock, store.db:
        store.db.execute(
            "UPDATE jobs SET lease_until=?, heartbeat_at=? WHERE job_id=?",
            ("2000-01-01T00:00:00+00:00", "2000-01-01T00:00:00+00:00", job.job_id),
        )

    assert store.recover_running_jobs() == 1
    fresh = store.claim(job.job_id, worker_id="worker-b")
    assert fresh is not None

    with pytest.raises(LeaseLostError):
        store.record_result(
            job.job_id,
            {"worker": "stale"},
            worker_id=stale.worker_id,
            lease_token=stale.lease_token,
        )

    store.record_result(
        job.job_id,
        {"worker": "fresh"},
        worker_id=fresh.worker_id,
        lease_token=fresh.lease_token,
    )
    assert store.get_checkpoint(job.job_id) == {"worker": "fresh"}
    assert store.get_result(job.job_id) is None
    store.close()


def test_stale_worker_cannot_finalize_failure_after_recovery(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db", lease_seconds=30)
    job = store.enqueue("demo", {})
    stale = store.claim(job.job_id, worker_id="worker-a")
    assert stale is not None

    with store.lock, store.db:
        store.db.execute(
            "UPDATE jobs SET lease_until=?, heartbeat_at=? WHERE job_id=?",
            ("2000-01-01T00:00:00+00:00", "2000-01-01T00:00:00+00:00", job.job_id),
        )

    assert store.recover_running_jobs() == 1
    fresh = store.claim(job.job_id, worker_id="worker-b")
    assert fresh is not None

    with pytest.raises(LeaseLostError):
        store.finish(
            job.job_id,
            False,
            "stale failure",
            retry=False,
            worker_id=stale.worker_id,
            lease_token=stale.lease_token,
        )

    current = store.get(job.job_id)
    assert current is not None
    assert current.status == "running"
    assert store.get_result(job.job_id) is None

    store.finish(
        job.job_id,
        False,
        "fresh failure",
        retry=False,
        worker_id=fresh.worker_id,
        lease_token=fresh.lease_token,
    )
    current = store.get(job.job_id)
    assert current is not None
    assert current.status == "failed"
    assert store.get_result(job.job_id) == {"ok": False, "error": "fresh failure"}
    store.close()
