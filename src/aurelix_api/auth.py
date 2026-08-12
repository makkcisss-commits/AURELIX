from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    subject: str
    scopes: frozenset[str]


def require_scope(principal: AuthenticatedPrincipal, scope: str) -> None:
    if scope not in principal.scopes:
        raise PermissionError(f"missing required scope: {scope}")
