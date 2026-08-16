from aurelix_runtime import AurelixSystem, SystemConfig
from aurelix_runtime.runtime import RuntimeConfig


def test_production_style_system_has_one_autonomous_schedule(tmp_path):
    calls = []

    def cycle_handler(objective: str):
        calls.append(objective)
        return {"status": "ok", "objective": objective}

    # This test exercises explicit schedule registration; the production
    # default economic schedule is intentionally disabled for isolation.
    system = AurelixSystem(
        SystemConfig(
            runtime=RuntimeConfig(
                database_path=str(tmp_path / "system.db"),
                heartbeat_seconds=2,
                worker_poll_seconds=0.01,
            ),
            enable_autonomy=False,
        ),
        cycle_handler=cycle_handler,
    )
    try:
        assert system.health()["schedules"] == []
        system.schedule_system_cycle("default-autonomy", 1, "find verified revenue")
        assert system.health()["schedules"] == ["default-autonomy"]
        system.start()
        system.tick()
        assert calls == ["find verified revenue"]
    finally:
        system.close()


def test_standalone_system_keeps_runtime_autonomy_schedule(tmp_path):
    system = AurelixSystem(
        SystemConfig(
            runtime=RuntimeConfig(database_path=str(tmp_path / "system.db")),
            enable_autonomy=True,
        )
    )
    try:
        assert system.health()["schedules"] == ["economic-discovery"]
    finally:
        system.close()
