from aurelix_core.dashboard_service import DashboardService
from aurelix_core.system_snapshot import SystemSnapshot


def test_dashboard_service_is_read_only() -> None:
    service = DashboardService(SystemSnapshot())
    assert service.get_health() == {"status": "healthy"}
    snapshot = service.get_snapshot()
    assert snapshot["governor"] == "OPERATIONAL"
    assert snapshot["execution"] == "GUARDED"
    assert not hasattr(service, "execute")
    assert not hasattr(service, "approve")
