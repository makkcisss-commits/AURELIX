from aurelix_core.control_center import ComponentStatus, HealthState, build_snapshot


def test_verified_components_produce_healthy_snapshot() -> None:
    snapshot = build_snapshot([
        ComponentStatus("Governor", HealthState.HEALTHY, "policy gate operational"),
        ComponentStatus("Audit", HealthState.HEALTHY, "audit sink operational"),
        ComponentStatus("Private API", HealthState.HEALTHY, "API boundary operational"),
    ])
    assert snapshot.system is HealthState.HEALTHY
    assert snapshot.all_healthy


def test_non_healthy_component_marks_system_attention() -> None:
    snapshot = build_snapshot([
        ComponentStatus("Governor", HealthState.HEALTHY, "operational"),
        ComponentStatus("Treasury", HealthState.ATTENTION, "approval required"),
    ])
    assert snapshot.system is HealthState.ATTENTION
    assert not snapshot.all_healthy
