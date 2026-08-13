from threading import Barrier, Thread

from aurelix_runtime.persistence import RuntimeStore


def test_running_job_recovers_once_after_restart(tmp_path):
    db = tmp_path / "runtime.db"
    first = RuntimeStore(db)
    job = first.enqueue("demo", {"value": "1"})
    claimed = first.claim_next(worker_id="worker-1")
    assert claimed is not None
    assert claimed.job_id == job.job_id
    assert claimed.attempts == 1
    first.close()

    second = RuntimeStore(db)
    assert second.recover_running_jobs() == 1
    recovered = second.claim_next(worker_id="worker-2")
    assert recovered is not None
    assert recovered.job_id == job.job_id
    assert recovered.attempts == 2

    second.finish(recovered.job_id, True, result={"ok": True, "value": 42}, worker_id=recovered.worker_id, lease_token=recovered.lease_token)
    assert second.get_result(job.job_id) == {"ok": True, "value": 42}
    assert second.complete(job.job_id, {"ok": True, "value": 999}) == {"ok": True, "value": 42}
    assert second.get_result(job.job_id) == {"ok": True, "value": 42}
    second.close()


def test_finished_job_is_idempotent_when_finished_twice(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db")
    job = store.enqueue("demo", {})
    claimed = store.claim_next(worker_id="worker-1")
    assert claimed is not None
    store.finish(job.job_id, True, result={"ok": True}, worker_id=claimed.worker_id, lease_token=claimed.lease_token)

    # A repeated terminal acknowledgement must be safe and must not create a duplicate result.
    store.finish(job.job_id, True, result={"ok": False, "unexpected": True}, worker_id=claimed.worker_id, lease_token=claimed.lease_token)
    assert store.get(job.job_id).status == "completed"
    assert store.get_result(job.job_id) == {"ok": True}
    store.close()


def test_failure_never_becomes_success(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db")
    job = store.enqueue("demo", {})
    claimed = store.claim_next(worker_id="worker-1")
    assert claimed is not None
    store.finish(job.job_id, False, "boom", retry=False, worker_id=claimed.worker_id, lease_token=claimed.lease_token)
    assert store.get(job.job_id).status == "failed"
    assert store.get_result(job.job_id) == {"ok": False, "error": "boom"}
    try:
        store.complete(job.job_id, {"ok": True})
    except RuntimeError as exc:
        assert "cannot complete" in str(exc)
    else:
        raise AssertionError("a failed execution must never become successful")
    store.close()


def test_two_workers_cannot_claim_same_job(tmp_path):
    db = tmp_path / "runtime.db"
    seed = RuntimeStore(db)
    job = seed.enqueue("demo", {})
    seed.close()

    barrier = Barrier(2)
    results = []

    def worker(worker_id):
        store = RuntimeStore(db)
        barrier.wait()
        results.append(store.claim_next(worker_id=worker_id))
        store.close()

    threads = [Thread(target=worker, args=("worker-a",)), Thread(target=worker, args=("worker-b",))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    claimed_ids = [item.job_id for item in results if item is not None]
    assert claimed_ids == [job.job_id]
