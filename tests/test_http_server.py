from aurelix_core.dashboard_service import DashboardService
from aurelix_core.http_server import PrivateReadOnlyApi, ReadOnlyRequest
from aurelix_core.identity import Identity, register_secret
from aurelix_core.system_snapshot import SystemSnapshot


def test_authenticated_snapshot_endpoint_returns_dashboard_state() -> None:
    identity = Identity("owner", "owner")
    credential = register_secret(identity.id, "secret")
    api = PrivateReadOnlyApi(DashboardService(SystemSnapshot()))

    response = api.get_snapshot(ReadOnlyRequest(identity, credential, "secret"))

    assert response.status == 200
    assert response.body["governor"] == "OPERATIONAL"
    assert response.body["execution"] == "GUARDED"


def test_snapshot_endpoint_rejects_invalid_credentials() -> None:
    identity = Identity("owner", "owner")
    credential = register_secret(identity.id, "secret")
    api = PrivateReadOnlyApi(DashboardService(SystemSnapshot()))

    response = api.get_snapshot(ReadOnlyRequest(identity, credential, "wrong"))

    assert response.status == 401
    assert response.body == {"error": "authentication_failed"}


def test_routes_contain_no_mutating_endpoint() -> None:
    api = PrivateReadOnlyApi(DashboardService(SystemSnapshot()))
    routes = api.get_routes()
    assert "GET /v1/control/snapshot" in routes
    assert all(not route.startswith(("POST ", "PUT ", "PATCH ", "DELETE ")) for route in routes)
