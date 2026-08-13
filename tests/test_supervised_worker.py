from aurelix_runtime.job_queue import PersistentJobQueue
from aurelix_runtime.supervised_worker import SupervisedWorker, WorkerConfig


def test_supervised_worker_processes_queued_job_and_heartbeats(tmp_path):
    from aurelix_runtime.persistence import RuntimeStore

    queue = PersistentJobQueue(RuntimeStore(tmp_path / "runtime.db"))
    queue.enqueue("job-1", "objective")
    worker = SupervisedWorker(queue, WorkerConfig(max_jobs=1, max_attempts=2))
    processed = worker.run_once()
    assert processed == ["job-1"]
    assert worker.heartbeat_count == 1
    assert queue.jobs["job-1"].status == "completed"
    assert queue.store.get_result("job-1")["status"] == "awaiting_approval"
    queue.close()


def test_worker_recovery_requeues_running_jobs(tmp_path):
    from aurelix_runtime.persistence import RuntimeStore

    queue = PersistentJobQueue(RuntimeStore(tmp_path / "runtime.db"))
    queue.enqueue("job-2", "objective")
    queue.claim("job-2")
    worker = SupervisedWorker(queue)
    assert worker.recover() == 1
    assert queue.jobs["job-2"].status == "queued"
    queue.close()
