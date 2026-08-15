from aurelix_core.dashboard_service import DashboardService
from aurelix_core.system_snapshot import SystemSnapshot


def test_dashboard_service_is_read_only() -> None:
    service = DashboardService(SystemSnapshot())
    assert service.get_health() == {"status": "unverified"}


def test_dashboard_service_does_not_mutate_snapshot() -> None:
    snapshot = SystemSnapshot()
    service = DashboardService(snapshot)
    assert service.get_snapshot() == snapshot.public()
