from decimal import Decimal

from aurelix_core.control_center import ComponentStatus, ControlCenter, HealthState, build_snapshot
from aurelix_core.governor import Governor
from aurelix_core.revenue import RevenueEngine
from aurelix_core.treasury import Treasury


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


def test_control_center_snapshot_is_read_only() -> None:
    treasury = Treasury(Decimal("100"))
    revenue = RevenueEngine()
    revenue.record(activity_id="activity-1", amount_eur=Decimal("250"), source="invoice")
    center = ControlCenter(treasury=treasury, revenue=revenue, governor=Governor())
    snapshot = center.snapshot([
        ComponentStatus("Treasury", HealthState.HEALTHY, "operational"),
        ComponentStatus("Revenue", HealthState.HEALTHY, "operational"),
    ])
    assert snapshot.treasury_free_eur == "100"
    assert snapshot.revenue_total_eur == "250"
    assert treasury.snapshot().free_eur == Decimal("100")
