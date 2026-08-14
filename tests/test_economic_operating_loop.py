import pytest

from aurelix_core.engine_factory import EngineFactory, EngineFactoryConfig
from aurelix_runtime.message_fabric import AgentMessage, MessageFabric
from aurelix_runtime.mission_contracts import DEFAULT_ECONOMIC_TASKS, EconomicMission, MissionState
from aurelix_runtime.runtime import RuntimeConfig
from aurelix_runtime.system import AurelixSystem, SystemConfig


def test_message_fabric_is_idempotent_and_structured():
    fabric = MessageFabric()
    received = []
    fabric.subscribe("work", received.append)
    message = AgentMessage(topic="work", sender="academy", payload={"objective": "x"}, idempotency_key="same")
    assert len(fabric.publish(message)) == 1
    assert fabric.publish(message) == []
    assert received[0].sender == "academy"
    assert received[0].correlation_id


def test_economic_mission_enforces_order_and_evidence():
    mission = EconomicMission("find a real revenue opportunity")
    mission.plan(list(DEFAULT_ECONOMIC_TASKS))
    assert mission.state is MissionState.PLANNED
    mission.start()
    assert mission.state is MissionState.RUNNING
    with pytest.raises(ValueError):
        mission.complete([])
    mission.complete([{"type": "verified-opportunity", "verified": True}])
    assert mission.state is MissionState.COMPLETED


def test_system_has_one_ordered_autonomous_economic_loop(tmp_path):
    system = AurelixSystem(SystemConfig(
        runtime=RuntimeConfig(database_path=str(tmp_path / "aurelix.db")),
        enable_autonomy=True,
        economic_cycle_seconds=900,
    ))
    try:
        health = system.health()
        assert health["fabric"] == "structured-topic-router"
        assert health["mission"]["state"] == "planned"
        assert "economic-discovery" in health["schedules"]
        system.start()
        assert system.health()["status"] == "running"
        rows = system.store.db.execute(
            "SELECT event_type FROM audit_log WHERE event_type='fabric.mission_created'"
        ).fetchall()
        assert rows
    finally:
        system.close()


def test_factory_backed_system_uses_the_canonical_cycle_and_shared_fabric(tmp_path):
    factory = EngineFactory(EngineFactoryConfig(
        runtime=RuntimeConfig(database_path=str(tmp_path / "aurelix.db")),
        register_autonomy=True,
    ))
    system = AurelixSystem(SystemConfig(
        runtime=RuntimeConfig(database_path=str(tmp_path / "unused.db")),
        enable_autonomy=True,
        economic_cycle_seconds=900,
    ), factory=factory)
    try:
        health = system.health()
        assert health["composition"] == "engine-factory"
        assert health["fabric"] == "shared-composition-fabric"
        assert "economic-discovery" in health["schedules"]
        assert "system.cycle" in factory.runtime.handlers
        assert system.fabric is factory.message_fabric
        assert system.governor is factory.governor
    finally:
        system.close()
        factory.runtime.close()
