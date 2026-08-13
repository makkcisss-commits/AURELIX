from threading import Barrier, Thread
from aurelix_runtime.persistence import RuntimeStore

def test_running_job_recovers_once_after_restart(tmp_path):
    db = tmp_path / "runtime.db"; first = RuntimeStore(db); job = first.enqueue("demo", {"value": "1"}); claimed = first.claim_next(worker_id="worker-1")
    assert claimed is not None and claimed.job_id == job.job_id and claimed.attempts == 1; first.close()
    second = RuntimeStore(db); assert second.recover_running_jobs(stale_after_seconds=0) == 1
    recovered = second.claim_next(worker_id="worker-2"); assert recovered is not None and recovered.job_id == job.job_id and recovered.attempts == 2
    second.finish(recovered.job_id, True, result={"ok": True, "value": 42}, worker_id=recovered.worker_id, lease_token=recovered.lease_token)
    assert second.get_result(job.job_id) == {"ok": True, "value": 42}; assert second.complete(job.job_id, {"ok": True, "value": 999}) == {"ok": True, "value": 42}; second.close()

def test_finished_job_cannot_be_finished_twice(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db"); job = store.enqueue("demo", {}); claimed = store.claim_next(worker_id="worker-1"); assert claimed is not None
    store.finish(job.job_id, True, worker_id=claimed.worker_id, lease_token=claimed.lease_token)
    try: store.finish(job.job_id, True, worker_id=claimed.worker_id, lease_token=claimed.lease_token)
    except RuntimeError as exc: assert "cannot finish" in str(exc)
    else: raise AssertionError("a completed job must not be finished twice")
    store.close()

def test_failure_never_becomes_success(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db"); job = store.enqueue("demo", {}); claimed = store.claim_next(worker_id="worker-1"); assert claimed is not None
    store.finish(job.job_id, False, "boom", retry=False, worker_id=claimed.worker_id, lease_token=claimed.lease_token)
    assert store.get(job.job_id).status == "failed"; assert store.get_result(job.job_id) == {"ok": False, "error": "boom"}
    try: store.complete(job.job_id, {"ok": True}, worker_id=claimed.worker_id, lease_token=claimed.lease_token)
    except RuntimeError as exc: assert "cannot complete" in str(exc)
    else: raise AssertionError("a failed execution must never become successful")
    store.close()

def test_two_workers_cannot_claim_same_job(tmp_path):
    db = tmp_path / "runtime.db"; seed = RuntimeStore(db); job = seed.enqueue("demo", {}); seed.close(); barrier = Barrier(2); results = []
    def worker():
        store = RuntimeStore(db); barrier.wait(); results.append(store.claim_next(worker_id="concurrent-worker")); store.close()
    threads = [Thread(target=worker), Thread(target=worker)]
    for thread in threads: thread.start()
    for thread in threads: thread.join()
    claimed_ids = [item.job_id for item in results if item is not None]; assert claimed_ids == [job.job_id]
