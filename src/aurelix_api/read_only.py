from __future__ import annotations

from dataclasses import asdict

from aurelix_core.control_center import ControlCenter, ControlCenterSnapshot

from .auth import AuthenticatedPrincipal, require_scope


class ReadOnlyControlAPI:
    """Application boundary for authenticated, read-only Control Center access."""

    def __init__(self, control_center: ControlCenter) -> None:
        self._control_center = control_center

    def get_snapshot(self, principal: AuthenticatedPrincipal) -> dict:
        require_scope(principal, "control:read")
        snapshot: ControlCenterSnapshot = self._control_center.snapshot()
        return asdict(snapshot)
