import pytest

from aurelix_runtime.job_queue import PersistentJobQueue
from aurelix_runtime.persistence import RuntimeStore
from aurelix_runtime.service import RuntimeConfig, RuntimeService


def test_runtime_lifecycle_and_job_execution(tmp_path):
    queue = PersistentJobQueue(RuntimeStore(tmp_path / "runtime.db"))
    queue.enqueue("job-1", "objective")
    runtime = RuntimeService(queue, RuntimeConfig(tick_seconds=0.01))
    assert runtime.status == "stopped"
    runtime.start()
    assert runtime.status == "running"
    runtime.tick()
    assert queue.jobs["job-1"].status == "completed"
    assert queue.store.get_result("job-1")["status"] == "awaiting_approval"
    runtime.stop()
    assert runtime.status == "stopping"
    queue.close()


def test_runtime_requires_start_before_tick(tmp_path):
    queue = PersistentJobQueue(RuntimeStore(tmp_path / "runtime.db"))
    runtime = RuntimeService(queue)
    with pytest.raises(RuntimeError):
        runtime.tick()
    queue.close()
