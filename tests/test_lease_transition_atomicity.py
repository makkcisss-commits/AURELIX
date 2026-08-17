import pytest
from datetime import datetime, timedelta, timezone

from aurelix_runtime.persistence import LeaseLostError, RuntimeStore


def test_failure_finalization_clears_lease_and_persists_terminal_result(tmp_path) -> None:
    store = RuntimeStore(tmp_path / "failure-finalization.db")
    try:
        queued = store.enqueue("lease-failure", execution_id="exec-failure")
        claimed = store.claim(queued.job_id, worker_id="worker-a")
        assert claimed is not None

        store.fail(
            claimed.job_id,
            "provider failed",
            retry=False,
            worker_id="worker-a",
            lease_token=claimed.lease_token,
        )

        record = store.get(claimed.job_id)
        assert record is not None
        assert record.status == "failed"
        assert record.worker_id is None
        assert record.lease_token is None
        assert record.lease_until is None
        assert store.get_result(claimed.job_id) == {"ok": False, "error": "provider failed"}
    finally:
        store.close()


def test_checkpoint_cannot_cross_a_terminal_lease_boundary(tmp_path) -> None:
    store = RuntimeStore(tmp_path / "checkpoint-fencing.db")
    try:
        queued = store.enqueue("checkpoint", execution_id="exec-checkpoint")
        claimed = store.claim(queued.job_id, worker_id="worker-a")
        assert claimed is not None
        store.record_result(
            claimed.job_id,
            {"step": 1},
            worker_id="worker-a",
            lease_token=claimed.lease_token,
        )
        store.fail(
            claimed.job_id,
            "terminal failure",
            retry=False,
            worker_id="worker-a",
            lease_token=claimed.lease_token,
        )

        with pytest.raises(RuntimeError):
            store.record_result(
                claimed.job_id,
                {"step": 2},
                worker_id="worker-a",
                lease_token=claimed.lease_token,
            )
    finally:
        store.close()


def _expire_lease(store: RuntimeStore, job_id: str) -> None:
    expired = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    with store.lock, store.db:
        store.db.execute(
            "UPDATE jobs SET lease_until=?, heartbeat_at=? WHERE job_id=?",
            (expired, expired, job_id),
        )


def test_expired_lease_cannot_complete_job(tmp_path) -> None:
    store = RuntimeStore(tmp_path / "expired-complete.db")
    try:
        queued = store.enqueue("expired-complete", execution_id="exec-expired-complete")
        claimed = store.claim(queued.job_id, worker_id="worker-a")
        assert claimed is not None
        _expire_lease(store, claimed.job_id)

        with pytest.raises(LeaseLostError):
            store.complete(
                claimed.job_id,
                {"ok": True},
                worker_id="worker-a",
                lease_token=claimed.lease_token,
            )

        record = store.get(claimed.job_id)
        assert record is not None
        assert record.status == "running"
        assert store.get_result(claimed.job_id) is None
    finally:
        store.close()


def test_expired_lease_cannot_finalize_failure(tmp_path) -> None:
    store = RuntimeStore(tmp_path / "expired-failure.db")
    try:
        queued = store.enqueue("expired-failure", execution_id="exec-expired-failure")
        claimed = store.claim(queued.job_id, worker_id="worker-a")
        assert claimed is not None
        _expire_lease(store, claimed.job_id)

        with pytest.raises(LeaseLostError):
            store.fail(
                claimed.job_id,
                "late failure",
                retry=False,
                worker_id="worker-a",
                lease_token=claimed.lease_token,
            )

        record = store.get(claimed.job_id)
        assert record is not None
        assert record.status == "running"
        assert store.get_result(claimed.job_id) is None
    finally:
        store.close()
