from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .dashboard_service import DashboardService
from .identity import AuthenticationError, CredentialRecord, Identity, authenticate
from .http_contract import ApiResponse, health_response, readiness_response, safe_error_response


@dataclass(frozen=True)
class ReadOnlyRequest:
    identity: Identity
    credential: CredentialRecord
    secret: str


class PrivateReadOnlyApi:
    """Authenticated, read-only HTTP-facing application contract."""

    def __init__(
        self,
        dashboard: DashboardService,
        experiments: Callable[[str | None], list[dict[str, Any]]] | None = None,
        knowledge: Callable[[str, int], list[dict[str, Any]]] | None = None,
        audit: Callable[[int], list[dict[str, Any]]] | None = None,
    ) -> None:
        self.dashboard = dashboard
        self.experiments = experiments
        self.knowledge = knowledge
        self.audit = audit

    def _authenticate(self, request: ReadOnlyRequest) -> ApiResponse | None:
        try:
            authenticate(request.identity, request.credential, request.secret)
        except AuthenticationError:
            return safe_error_response(401, "authentication_failed")
        return None

    def get_health(self) -> ApiResponse:
        return health_response()

    def get_readiness(self, ready: bool = True) -> ApiResponse:
        return readiness_response(ready)

    def get_snapshot(self, request: ReadOnlyRequest) -> ApiResponse:
        error = self._authenticate(request)
        if error:
            return error
        return ApiResponse(200, self.dashboard.get_snapshot())

    def get_experiments(self, request: ReadOnlyRequest, status: str | None = None) -> ApiResponse:
        error = self._authenticate(request)
        if error:
            return error
        if self.experiments is None:
            return safe_error_response(503, "experiments_unavailable")
        return ApiResponse(200, {"experiments": self.experiments(status)})

    def get_knowledge(self, request: ReadOnlyRequest, query: str = "", limit: int = 20) -> ApiResponse:
        error = self._authenticate(request)
        if error:
            return error
        if self.knowledge is None:
            return safe_error_response(503, "knowledge_unavailable")
        return ApiResponse(200, {"knowledge": self.knowledge(query, max(0, min(limit, 100)))})

    def get_audit(self, request: ReadOnlyRequest, limit: int = 50) -> ApiResponse:
        error = self._authenticate(request)
        if error:
            return error
        if self.audit is None:
            return safe_error_response(503, "audit_unavailable")
        return ApiResponse(200, {"events": self.audit(max(0, min(limit, 200)))})

    def get_routes(self) -> dict[str, str]:
        return {
            "GET /health": "public liveness only",
            "GET /ready": "readiness only",
            "GET /v1/control/snapshot": "authenticated read-only system snapshot",
            "GET /v1/control/experiments": "authenticated read-only experiment state",
            "GET /v1/control/knowledge": "authenticated read-only knowledge search",
            "GET /v1/control/audit": "authenticated read-only audit events",
        }
