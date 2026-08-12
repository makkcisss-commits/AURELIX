from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .dashboard_service import DashboardService
from .identity import AuthenticationError, CredentialRecord, Identity, authenticate
from .http_contract import ApiResponse, health_response, readiness_response, safe_error_response


@dataclass(frozen=True)
class ReadOnlyRequest:
    identity: Identity
    credential: CredentialRecord
    secret: str


class PrivateReadOnlyApi:
    """Authenticated, read-only HTTP-facing application contract.

    A real ASGI/WSGI server can adapt this class to HTTPS. TLS termination,
    rate limiting and secure transport configuration belong to deployment.
    """

    def __init__(self, dashboard: DashboardService) -> None:
        self.dashboard = dashboard

    def get_health(self) -> ApiResponse:
        return health_response()

    def get_readiness(self, ready: bool = True) -> ApiResponse:
        return readiness_response(ready)

    def get_snapshot(self, request: ReadOnlyRequest) -> ApiResponse:
        try:
            authenticate(request.identity, request.credential, request.secret)
        except AuthenticationError:
            return safe_error_response(401, "authentication_failed")
        return ApiResponse(200, self.dashboard.get_snapshot())

    def get_routes(self) -> dict[str, str]:
        return {
            "GET /health": "public liveness only",
            "GET /ready": "readiness only",
            "GET /v1/control/snapshot": "authenticated read-only system snapshot",
        }
