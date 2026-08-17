import pytest

from aurelix_runtime.persistence import RuntimeStore


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
