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
