from threading import Barrier, Thread

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

    second.finish(recovered.job_id, True, result={"ok": True, "value": 42})
    assert second.get_result(job.job_id) == {"ok": True, "value": 42}
    assert second.complete(job.job_id, {"ok": True, "value": 999}) == {"ok": True, "value": 42}
    assert second.get_result(job.job_id) == {"ok": True, "value": 42}
    second.close()


def test_finished_job_cannot_be_finished_twice(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db")
    job = store.enqueue("demo", {})
    assert store.claim_next() is not None
    store.finish(job.job_id, True)

    try:
        store.finish(job.job_id, True)
    except RuntimeError as exc:
        assert "cannot finish" in str(exc)
    else:
        raise AssertionError("a completed job must not be finished twice")
    store.close()


def test_failure_never_becomes_success(tmp_path):
    store = RuntimeStore(tmp_path / "runtime.db")
    job = store.enqueue("demo", {})
    assert store.claim_next() is not None
    store.finish(job.job_id, False, "boom", retry=False)
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

    def worker():
        store = RuntimeStore(db)
        barrier.wait()
        results.append(store.claim_next())
        store.close()

    threads = [Thread(target=worker), Thread(target=worker)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    claimed_ids = [item.job_id for item in results if item is not None]
    assert claimed_ids == [job.job_id]
