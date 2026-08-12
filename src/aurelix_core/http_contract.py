from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ApiResponse:
    status: int
    body: dict[str, Any]


def health_response() -> ApiResponse:
    return ApiResponse(
        200,
        {
            "status": "ok",
            "service": "aurelix-private-api",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


def readiness_response(ready: bool) -> ApiResponse:
    if ready:
        return ApiResponse(200, {"status": "ready"})
    return ApiResponse(503, {"status": "not_ready"})


def safe_error_response(status: int, code: str) -> ApiResponse:
    return ApiResponse(status, {"error": code})
