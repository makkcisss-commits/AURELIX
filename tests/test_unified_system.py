from pathlib import Path

from aurelix_runtime import AurelixSystem, SystemConfig
from aurelix_runtime.runtime import RuntimeConfig


def test_unified_system_uses_one_store_and_executes_scheduled_autonomy(tmp_path: Path):
    system = AurelixSystem(SystemConfig(
        runtime=RuntimeConfig(
            database_path=str(tmp_path / "system.db"),
            heartbeat_seconds=2,
            worker_poll_seconds=0.01,
        )
    ))
    system.schedule_autonomy("integration", 1, "unified system integration")
    system.start()
    try:
        assert system.health()["store"] == "shared"
        job_id = system.submit("autonomy.run", {"objective": "direct integration"})
        assert system.tick() == ["runtime"]
        result = system.store.get_result(job_id)
        assert result is not None
        assert result["execution_id"] == job_id
        assert system.store.get(job_id).status == "completed"
    finally:
        system.close()


def test_unified_system_requires_start(tmp_path: Path):
    system = AurelixSystem(SystemConfig(
        runtime=RuntimeConfig(database_path=str(tmp_path / "system.db"))
    ))
    try:
        try:
            system.tick()
        except RuntimeError as exc:
            assert "not started" in str(exc)
        else:
            raise AssertionError("tick must require system.start()")
    finally:
        system.close()
