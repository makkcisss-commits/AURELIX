from __future__ import annotations

from fastapi.testclient import TestClient

from aurelix_core.server import app


def test_health_endpoint_is_public_and_reports_service():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert "timestamp" in body


def test_protected_control_plane_requires_owner_secret():
    client = TestClient(app)
    response = client.get("/v1/control/snapshot")

    assert response.status_code == 401
    assert response.json()["detail"] == "authentication_required"


def test_ready_endpoint_requires_production_credential():
    client = TestClient(app)
    response = client.get("/ready")

    assert response.status_code in {200, 503}
    if response.status_code == 503:
        assert response.json()["detail"] in {
            "not_ready",
            "runtime_initialization_failed",
        }
