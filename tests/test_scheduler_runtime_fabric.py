from pathlib import Path

from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig
from aurelix_runtime.scheduler import Schedule, Scheduler


def test_scheduler_uses_the_runtime_store_and_claimed_fabric(tmp_path: Path):
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "runtime.db"), heartbeat_seconds=2, worker_poll_seconds=0.01))
    runtime.register_autonomy()
    scheduler = Scheduler(submit=runtime.submit)
    scheduler.add(Schedule("autonomy", 1, "autonomy.run", {"objective": "scheduled integration"}))

    job_id = scheduler.submit("autonomy.run", {"objective": "scheduled integration"})
    assert scheduler.queue.store is runtime.store
    assert scheduler.tick() == ["runtime"]

    result = runtime.store.get_result(job_id)
    assert result is not None
    assert result["execution_id"] == job_id
    assert set(result) >= {
        "execution_id", "status", "research", "academy", "knowledge",
        "innovation", "experiment", "evaluation", "opportunity", "business",
    }
    assert runtime.store.get(job_id).status == "completed"
    scheduler.stop()
    runtime.close()
