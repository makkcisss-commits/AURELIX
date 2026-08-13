"""Unified validation gate for AURELIX capabilities and self-improvement."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Callable


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ValidationResult:
    name: str
    status: str
    evidence: dict[str, Any]
    checked_at: str


class SystemValidation:
    """Runs explicit capability checks and returns one machine-readable verdict."""

    def __init__(self, factory, checks: dict[str, Callable[[], Any]] | None = None) -> None:
        self.factory = factory
        self.checks = checks or {
            "health_registry": self._health,
            "runtime": self._runtime,
            "engine_factory": self._factory,
            "knowledge_store": self._knowledge,
        }

    def _health(self) -> dict[str, Any]:
        snapshot = self.factory.runtime.health.snapshot(self.factory.runtime.runtime_name)
        return {"status": snapshot.status, "components": snapshot.components}

    def _runtime(self) -> dict[str, Any]:
        runtime = self.factory.runtime
        return {"status": "ok" if runtime is not None else "failed", "runtime": type(runtime).__name__}

    def _factory(self) -> dict[str, Any]:
        required = ["research", "academy", "knowledge", "innovation", "experiment", "evaluation", "opportunity", "business"]
        missing = [name for name in required if not hasattr(self.factory, name)]
        return {"status": "ok" if not missing else "failed", "missing": missing}

    def _knowledge(self) -> dict[str, Any]:
        store = getattr(self.factory.runtime, "knowledge_store", None)
        return {"status": "ok" if store is not None else "degraded", "configured": store is not None}

    def run(self) -> dict[str, Any]:
        results: list[ValidationResult] = []
        for name, check in self.checks.items():
            try:
                evidence = check()
                status = evidence.get("status", "ok") if isinstance(evidence, dict) else "ok"
            except Exception as exc:
                evidence = {"error": type(exc).__name__}
                status = "failed"
            results.append(ValidationResult(name, status, evidence, _now()))
        failed = sum(r.status == "failed" for r in results)
        degraded = sum(r.status == "degraded" for r in results)
        overall = "failed" if failed else ("degraded" if degraded else "ok")
        report = {"status": overall, "summary": {"total": len(results), "failed": failed, "degraded": degraded, "ok": len(results) - failed - degraded}, "checks": [asdict(r) for r in results], "checked_at": _now()}
        self.factory.runtime.store.audit("system_validation.completed", "validation", "validate_system", overall, report["summary"])
        return report
