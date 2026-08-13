from aurelix_runtime.system import AurelixSystem, SystemConfig
from aurelix_runtime.runtime import RuntimeConfig


def test_system_routes_submission_through_shared_runtime(tmp_path):
    system = AurelixSystem(SystemConfig(runtime=RuntimeConfig(database_path=str(tmp_path / "aurelix.db")), enable_autonomy=False))
    try:
        system.runtime.register("unit", lambda payload: {"objective": payload["objective"]})
        system.start()
        job_id = system.submit("unit", {"objective": "test"})
        assert system.tick() == ["runtime"]
        assert system.store.get(job_id).status == "completed"
        assert system.store.get_result(job_id) == {"objective": "test"}
        assert system.health()["store"] == "shared"
    finally:
        system.close()


def test_system_schedule_enters_same_runtime(tmp_path):
    system = AurelixSystem(SystemConfig(runtime=RuntimeConfig(database_path=str(tmp_path / "aurelix.db")), enable_autonomy=False))
    try:
        system.runtime.register("autonomy.run", lambda payload: {"objective": payload["objective"]})
        system.start()
        system.schedule_autonomy("scan", 3600, "find opportunities")
        assert system.tick() == ["runtime"]
        rows = system.store.db.execute("SELECT status FROM jobs WHERE name='autonomy.run'").fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "completed"
    finally:
        system.close()
