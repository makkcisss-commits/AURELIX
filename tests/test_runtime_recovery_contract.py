from datetime import datetime, timedelta, timezone

import pytest

from aurelix_runtime.persistence import LeaseLostError, RuntimeStore


def test_stale_running_job_is_requeued_without_success(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db", lease_seconds=30)
    job = store.enqueue("demo", {"objective": "recover me"})
    claimed = store.claim(job.job_id, max_attempts=3, worker_id="dead-worker")
    assert claimed is not None

    stale = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    with store.lock, store.db:
        store.db.execute(
            "UPDATE jobs SET heartbeat_at=?, lease_until=?, updated_at=? WHERE job_id=?",
            (stale, stale, stale, job.job_id),
        )

    assert store.recover_running_jobs(max_attempts=3, stale_after_seconds=1) == 1
    recovered = store.get(job.job_id)
    assert recovered is not None
    assert recovered.status == "queued"
    assert store.get_result(job.job_id) is None

    retry = store.claim(job.job_id, max_attempts=3, worker_id="new-worker")
    assert retry is not None
    assert retry.attempts == 2
    store.finish(job.job_id, True, result={"ok": True}, worker_id=retry.worker_id, lease_token=retry.lease_token)
    assert store.get(job.job_id).status == "completed"
    assert store.get_result(job.job_id) == {"ok": True}
    store.close()


def test_recovery_after_max_attempts_is_terminal_failure(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db", lease_seconds=30)
    job = store.enqueue("demo", {})
    claimed = store.claim(job.job_id, max_attempts=1, worker_id="dead-worker")
    assert claimed is not None

    stale = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    with store.lock, store.db:
        store.db.execute(
            "UPDATE jobs SET heartbeat_at=?, lease_until=? WHERE job_id=?",
            (stale, stale, job.job_id),
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


def test_old_worker_is_fenced_after_recovery(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db", lease_seconds=30)
    job = store.enqueue("demo", {})
    old = store.claim(job.job_id, worker_id="worker-a")
    assert old is not None

    expired = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    with store.lock, store.db:
        store.db.execute("UPDATE jobs SET lease_until=?, heartbeat_at=? WHERE job_id=?", (expired, expired, job.job_id))
    assert store.recover_running_jobs(max_attempts=3) == 1

    new = store.claim(job.job_id, worker_id="worker-b")
    assert new is not None
    with pytest.raises(LeaseLostError):
        store.complete(job.job_id, {"worker": "old"}, worker_id=old.worker_id, lease_token=old.lease_token)

    assert store.heartbeat(job.job_id, old.worker_id, old.lease_token) is False
    assert store.complete(job.job_id, {"worker": "new"}, worker_id=new.worker_id, lease_token=new.lease_token) == {"worker": "new"}
    store.close()


def test_heartbeat_renews_lease_only_for_current_owner(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db", lease_seconds=30)
    job = store.enqueue("demo", {})
    claimed = store.claim(job.job_id, worker_id="worker-a")
    assert claimed is not None
    before = claimed.lease_until
    assert store.heartbeat(job.job_id, "worker-a", claimed.lease_token) is True
    renewed = store.get(job.job_id)
    assert renewed is not None
    assert renewed.lease_until != before
    assert store.heartbeat(job.job_id, "worker-b", claimed.lease_token) is False
    store.close()
