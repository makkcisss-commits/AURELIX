import pytest

from aurelix_runtime.persistence import LeaseLostError, RuntimeStore


def test_intermediate_checkpoint_is_not_terminal_result_or_recovery_proof(tmp_path):
    db = tmp_path / "runtime.db"
    store = RuntimeStore(db, lease_seconds=30)
    job = store.enqueue("checkpointed", {"step": 1})
    claimed = store.claim_next(worker_id="worker-1")
    assert claimed is not None

    store.record_result(
        job.job_id,
        {"step": 1, "value": "checkpoint"},
        worker_id=claimed.worker_id,
        lease_token=claimed.lease_token,
    )

    assert store.get_checkpoint(job.job_id) == {"step": 1, "value": "checkpoint"}
    assert store.get_result(job.job_id) is None

    store.close()
    reopened = RuntimeStore(db, lease_seconds=30)
    assert reopened.recover_running_jobs(stale_after_seconds=0) == 1
    recovered = reopened.get(job.job_id)
    assert recovered is not None
    assert recovered.status == "queued"
    assert reopened.get_result(job.job_id) is None
    assert reopened.get_checkpoint(job.job_id) == {"step": 1, "value": "checkpoint"}
    reopened.close()


def test_completion_replaces_checkpoint_semantically_and_cleans_it(tmp_path):
    db = tmp_path / "runtime.db"
    store = RuntimeStore(db)
    job = store.enqueue("checkpointed", {})
    claimed = store.claim_next(worker_id="worker-1")
    assert claimed is not None

    store.record_result(job.job_id, {"partial": True}, worker_id=claimed.worker_id, lease_token=claimed.lease_token)
    final = store.complete(job.job_id, {"ok": True, "value": 42}, worker_id=claimed.worker_id, lease_token=claimed.lease_token)

    assert final == {"ok": True, "value": 42}
    assert store.get_result(job.job_id) == {"ok": True, "value": 42}
    assert store.get_checkpoint(job.job_id) is None
    assert store.get(job.job_id).status == "completed"
    store.close()


def test_checkpoint_requires_current_lease(tmp_path):
    db = tmp_path / "runtime.db"
    store = RuntimeStore(db, lease_seconds=1)
    job = store.enqueue("checkpointed", {})
    claimed = store.claim_next(worker_id="worker-1")
    assert claimed is not None

    with pytest.raises(LeaseLostError):
        store.record_result(job.job_id, {"bad": True}, worker_id="worker-2", lease_token="wrong")

    store.close()
