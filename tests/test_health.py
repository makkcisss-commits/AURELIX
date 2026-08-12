from aurelix_runtime.health import HealthRegistry


def test_health_is_ok_when_all_components_are_ok() -> None:
    health = HealthRegistry()
    health.set("scheduler", "ok")
    health.set("knowledge", "ok")

    snapshot = health.snapshot("running")

    assert snapshot.status == "ok"
    assert snapshot.runtime == "running"
    assert snapshot.components == {"scheduler": "ok", "knowledge": "ok"}
    assert snapshot.checked_at


def test_health_becomes_degraded_when_component_fails() -> None:
    health = HealthRegistry()
    health.set("scheduler", "ok")
    health.set("database", "failed")

    assert health.snapshot("running").status == "degraded"


def test_empty_registry_is_unknown() -> None:
    assert HealthRegistry().snapshot("booting").status == "unknown"
