from pathlib import Path

from aurelix_runtime.runtime import AurelixRuntime, RuntimeConfig
from aurelix_runtime.scheduler import Schedule, Scheduler


def test_runtime_persists_and_runs_jobs(tmp_path: Path) -> None:
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "aurelix.db")))
    seen: list[dict[str, str]] = []
    runtime.register("academy.maintenance", seen.append)
    runtime.submit("academy.maintenance", {"mode": "scan"})
    assert runtime.run_once()
    assert seen == [{"mode": "scan"}]
    assert runtime.store.status()["succeeded"] == 1


def test_scheduler_only_enqueues_registered_work(tmp_path: Path) -> None:
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "aurelix.db")))
    runtime.register("research.heartbeat", lambda _: None)
    scheduler = Scheduler(runtime.submit)
    scheduler.add(Schedule("research", 1, "research.heartbeat", {}))
    scheduler.submit("research.heartbeat", {})
    assert runtime.run_once()


def test_scheduler_tick_uses_runtime_worker_when_bound(tmp_path: Path) -> None:
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "aurelix.db")))
    seen: list[dict[str, str]] = []
    runtime.register("pipeline.run", seen.append)
    scheduler = Scheduler(runtime.submit)
    scheduler.submit("pipeline.run", {"objective": "integrate"})
    assert scheduler.tick() == ["runtime"]
    assert seen == [{"objective": "integrate"}]


def test_autonomy_is_a_single_runtime_job(tmp_path: Path, monkeypatch) -> None:
    from aurelix_runtime import autonomy_fabric

    class FakeFabric:
        def __init__(self, store=None):
            self.store = store

        def run_claimed(self, claimed):
            assert claimed.status == "running"
            assert claimed.worker_id
            assert claimed.lease_token
            return {
                "execution_id": claimed.job_id,
                "status": "completed",
                "research": {}, "academy": {}, "knowledge": {}, "innovation": {},
                "experiment": {}, "evaluation": {}, "opportunity": {}, "business": {},
            }

    monkeypatch.setattr(autonomy_fabric, "AutonomyFabric", FakeFabric)
    runtime = AurelixRuntime(RuntimeConfig(database_path=str(tmp_path / "aurelix.db"), heartbeat_seconds=2))
    runtime.register_autonomy()
    job_id = runtime.submit("autonomy.run", {"objective": "find opportunities"})
    assert runtime.run_once()
    assert runtime.store.get(job_id).status == "completed"
    assert runtime.store.get_result(job_id)["execution_id"] == job_id
