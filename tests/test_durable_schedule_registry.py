from pathlib import Path

from aurelix_runtime.runtime import RuntimeConfig
from aurelix_runtime.system import AurelixSystem, SystemConfig


def test_schedule_definition_survives_system_restart(tmp_path: Path) -> None:
    database = tmp_path / "aurelix.db"
    config = SystemConfig(runtime=RuntimeConfig(database_path=str(database)), enable_autonomy=False)

    first = AurelixSystem(config)
    try:
        first.schedule_autonomy("durable-discovery", 37, "find verified opportunities")
        assert [s.name for s in first.scheduler.schedules] == ["durable-discovery"]
    finally:
        first.close()

    second = AurelixSystem(config)
    try:
        schedules = [s for s in second.scheduler.schedules if s.name == "durable-discovery"]
        assert len(schedules) == 1
        assert schedules[0].interval_seconds == 37
        assert schedules[0].job_kind == "autonomy.run"
        assert schedules[0].payload == {"objective": "find verified opportunities"}
    finally:
        second.close()
