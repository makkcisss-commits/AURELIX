from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .audit import AuditEvent, AuditLog
from .identity import AuthenticationError, CredentialRecord, Identity, authenticate


class ApiDenied(Exception):
    """Raised when an API request is not authenticated or permitted."""


@dataclass(frozen=True)
class ApiPrincipal:
    identity: Identity


class PrivateApi:
    """Framework-neutral private API boundary.

    This layer authenticates a caller before dispatching to an explicitly
    registered operation. It intentionally has no HTTP server and no arbitrary
    dynamic dispatch. A web adapter can be placed above it later.
    """

    def __init__(self, audit: AuditLog) -> None:
        self.audit = audit
        self._routes: dict[str, Callable[[ApiPrincipal, object], object]] = {}

    def register(self, name: str, handler: Callable[[ApiPrincipal, object], object]) -> None:
        if not name or name in self._routes:
            raise ValueError("API operation name must be unique and non-empty")
        self._routes[name] = handler

    def call(
        self,
        identity: Identity,
        credential: CredentialRecord,
        secret: str,
        operation: str,
        payload: object = None,
    ) -> object:
        try:
            principal = ApiPrincipal(authenticate(identity, credential, secret))
        except AuthenticationError as exc:
            self.audit.append(
                AuditEvent(
                    event_type="api.authentication_denied",
                    actor_id=identity.id,
                    subject_id=operation,
                    outcome="denied",
                    metadata={"reason": str(exc)},
                )
            )
            raise ApiDenied("authentication failed") from exc

        handler = self._routes.get(operation)
        if handler is None:
            self.audit.append(
                AuditEvent(
                    event_type="api.operation_denied",
                    actor_id=identity.id,
                    subject_id=operation,
                    outcome="denied",
                    metadata={"reason": "unknown operation"},
                )
            )
            raise ApiDenied("unknown operation")

        result = handler(principal, payload)
        self.audit.append(
            AuditEvent(
                event_type="api.operation_completed",
                actor_id=identity.id,
                subject_id=operation,
                outcome="success",
            )
        )
        return result
