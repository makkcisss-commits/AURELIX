"""Local, dependency-light system doctor for AURELIX."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class SystemDoctor:
    """Runs the same observable checks without requiring external CI services."""

    def __init__(self, factory) -> None:
        self.factory = factory

    def run(self) -> dict[str, Any]:
        checks: list[dict[str, Any]] = []
        checks.append(self._check("runtime", lambda: self.factory.runtime is not None))
        checks.append(self._check("diagnostics", lambda: self.factory.diagnostics is not None))
        checks.append(self._check("validation", lambda: self.factory.system_validation is not None))
        checks.append(self._check("self_improvement", lambda: self.factory.self_improvement is not None))
        checks.append(self._check("enterprise_loop", lambda: self.factory.enterprise is not None))
        checks.append(self._check("economic_feedback", lambda: self.factory.economic_feedback is not None))
        failed = sum(c["status"] == "failed" for c in checks)
        return {
            "status": "failed" if failed else "ok",
            "summary": {"total": len(checks), "failed": failed, "ok": len(checks) - failed},
            "checks": checks,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _check(name: str, fn) -> dict[str, Any]:
        try:
            ok = bool(fn())
            return {"name": name, "status": "ok" if ok else "failed"}
        except Exception as exc:
            return {"name": name, "status": "failed", "error": type(exc).__name__}
