from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from .identity import CredentialRecord, Identity
from .private_api import ApiDenied, PrivateApi


@dataclass(frozen=True)
class ApiResponse:
    status_code: int
    body: dict[str, Any]


class PrivateTransport:
    """Minimal transport adapter kept independent from any web framework.

    A real HTTPS server should adapt requests into this boundary. It must not
    expose the Core directly or accept arbitrary operation names from clients.
    """

    def __init__(self, api: PrivateApi) -> None:
        self.api = api

    def handle(
        self,
        identity: Identity,
        credential: CredentialRecord,
        secret: str,
        operation: str,
        payload: object = None,
    ) -> ApiResponse:
        try:
            result = self.api.call(identity, credential, secret, operation, payload)
            return ApiResponse(200, {"ok": True, "data": result})
        except ApiDenied:
            # Do not disclose whether authentication or operation lookup failed.
            return ApiResponse(403, {"ok": False, "error": "forbidden"})
        except (TypeError, ValueError, json.JSONDecodeError):
            return ApiResponse(400, {"ok": False, "error": "invalid_request"})
