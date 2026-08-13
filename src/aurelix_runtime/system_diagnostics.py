"""Self-diagnostics for the connected AURELIX enterprise system."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Callable


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class DiagnosticCheck:
    name: str
    status: str
    severity: str
    detail: str
    evidence: dict[str, Any]


class SystemDiagnostics:
    """Runs bounded, observable checks across the system composition root."""

    def __init__(self, factory) -> None:
        self.factory = factory

    def run(self) -> dict[str, Any]:
        checks: list[DiagnosticCheck] = []
        checks.append(self._check("runtime", self._runtime))
        checks.append(self._check("model_provider", lambda: self._provider("model_provider")))
        checks.append(self._check("research_provider", lambda: self._provider("research_provider")))
        checks.append(self._check("knowledge_store", self._knowledge))
        checks.append(self._check("enterprise_loop", self._enterprise_loop))
        checks.append(self._check("developer_control", self._developer_control))
        failed = [c for c in checks if c.status == "failed"]
        degraded = [c for c in checks if c.status == "degraded"]
        overall = "failed" if failed else "degraded" if degraded else "ok"
        return {
            "status": overall,
            "checked_at": _now(),
            "checks": [asdict(c) for c in checks],
            "summary": {"total": len(checks), "failed": len(failed), "degraded": len(degraded)},
            "next_actions": self._next_actions(checks),
        }

    def _check(self, name: str, fn: Callable[[], DiagnosticCheck]) -> DiagnosticCheck:
        try:
            return fn()
        except Exception as exc:
            return DiagnosticCheck(name, "failed", "high", f"check crashed: {type(exc).__name__}", {"error": str(exc)})

    def _runtime(self) -> DiagnosticCheck:
        status = self.factory.runtime.store.status()
        return DiagnosticCheck("runtime", "ok", "info", "durable runtime is reachable", {"status": status})

    def _provider(self, attr: str) -> DiagnosticCheck:
        provider = getattr(self.factory, attr)
        if provider is None:
            return DiagnosticCheck(attr, "degraded", "medium", "provider is not configured", {"configured": False})
        healthy = getattr(provider, "health", None)
        if callable(healthy) and not healthy():
            return DiagnosticCheck(attr, "failed", "high", "provider health check failed", {"configured": True})
        return DiagnosticCheck(attr, "ok", "info", "provider is configured", {"configured": True})

    def _knowledge(self) -> DiagnosticCheck:
        count = self.factory.knowledge.count()
        return DiagnosticCheck("knowledge_store", "ok", "info", "knowledge repository is reachable", {"count": count, "backend": type(self.factory.knowledge).__name__})

    def _enterprise_loop(self) -> DiagnosticCheck:
        chain = [self.factory.research, self.factory.academy, self.factory.knowledge_engine, self.factory.innovation, self.factory.experiment, self.factory.evaluation, self.factory.opportunity, self.factory.business]
        missing = [type(x).__name__ for x in chain if x is None]
        if missing:
            return DiagnosticCheck("enterprise_loop", "failed", "high", "required specialist is missing", {"missing": missing})
        return DiagnosticCheck("enterprise_loop", "ok", "info", "all specialist roles are composed", {"roles": [type(x).__name__ for x in chain]})

    def _developer_control(self) -> DiagnosticCheck:
        developer = getattr(self.factory, "system_developer", None)
        if developer is None:
            return DiagnosticCheck("developer_control", "failed", "high", "system developer is not composed", {})
        return DiagnosticCheck("developer_control", "ok", "info", "controlled change planner is available", {"approval_required": developer.approval_required})

    @staticmethod
    def _next_actions(checks: list[DiagnosticCheck]) -> list[str]:
        actions: list[str] = []
        for check in checks:
            if check.status == "failed":
                actions.append(f"repair:{check.name}")
            elif check.status == "degraded":
                actions.append(f"configure_or_validate:{check.name}")
        return actions
