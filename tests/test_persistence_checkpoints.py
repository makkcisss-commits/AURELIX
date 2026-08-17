from __future__ import annotations

from aurelix_runtime.persistence import RuntimeStore


def test_intermediate_checkpoint_does_not_mark_job_completed_after_recovery(tmp_path):
    db_path = tmp_path / "runtime.db"
    first = RuntimeStore(db_path)
    first.enqueue("recoverable", {"step": 1}, execution_id="exec-1")
    claimed = first.claim("exec-1", worker_id="worker-a")
    assert claimed is not None
    first.record_result("exec-1", {"checkpoint": "step-1"}, worker_id="worker-a", lease_token=claimed.lease_token)
    assert first.get_result("exec-1") is None
    assert first.get_checkpoint("exec-1") == {"checkpoint": "step-1"}
    first.close()

    second = RuntimeStore(db_path)
    assert second.recover_running_jobs(stale_after_seconds=0) == 1
    recovered = second.get("exec-1")
    assert recovered is not None
    assert recovered.status == "queued"
    assert second.get_result("exec-1") is None
    assert second.get_checkpoint("exec-1") == {"checkpoint": "step-1"}
    second.close()
