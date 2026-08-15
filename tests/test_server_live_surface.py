from fastapi.testclient import TestClient

from aurelix_core.server import app


def test_health_and_web_surface_are_reachable():
    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    page = client.get("/")
    assert page.status_code == 200
    assert "AURELIX" in page.text
    # The public landing surface must never expose the owner credential.
    assert "owner-secret" not in page.text


def test_protected_snapshot_requires_owner_secret():
    client = TestClient(app)

    response = client.get("/v1/control/snapshot")
    assert response.status_code == 401
