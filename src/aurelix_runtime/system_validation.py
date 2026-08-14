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
            "canonical_composition": self._composition,
            "durable_experiment_execution": self._experiment_execution,
            "economic_feedback": self._economic_feedback,
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

    def _composition(self) -> dict[str, Any]:
        fabric = getattr(self.factory, "autonomy_fabric", None)
        enterprise = getattr(self.factory, "enterprise", None)
        if not self.factory.config.register_autonomy:
            return {"status": "degraded", "reason": "autonomy_disabled"}
        if fabric is None or enterprise is None:
            return {"status": "failed", "reason": "canonical_fabric_missing"}
        shared = {
            "engine_store": fabric.engines is enterprise.store,
            "message_fabric": fabric.message_fabric is self.factory.message_fabric,
            "research": fabric.research is self.factory.research,
            "academy": fabric.academy is self.factory.academy,
            "knowledge": fabric.knowledge is self.factory.knowledge_engine,
            "innovation": fabric.innovation is self.factory.innovation,
            "experiment": fabric.experiment is self.factory.experiment,
            "evaluation": fabric.evaluation is self.factory.evaluation,
            "opportunity": fabric.opportunity is self.factory.opportunity,
            "business": fabric.business is self.factory.business,
            "experiment_runner": fabric.experiment_runner is self.factory.experiment_runner,
            "adaptive_loop": fabric.adaptive_loop is self.factory.adaptive_loop,
            "capability_escalator": fabric.capability_escalator is self.factory.capability_escalator,
        }
        return {"status": "ok" if all(shared.values()) else "failed", "shared": shared}

    def _experiment_execution(self) -> dict[str, Any]:
        runner = getattr(self.factory, "experiment_runner", None)
        executor = getattr(self.factory, "experiment_executor", None)
        runtime = getattr(self.factory, "runtime", None)
        handlers = getattr(runtime, "handlers", {}) if runtime is not None else {}
        if runner is None:
            return {"status": "failed", "reason": "experiment_runner_missing"}
        if executor is None:
            return {"status": "failed", "reason": "real_experiment_executor_missing"}
        if "experiment.run" not in handlers:
            return {"status": "failed", "reason": "experiment_run_job_not_registered"}
        fabric = getattr(self.factory, "autonomy_fabric", None)
        if fabric is not None and fabric.experiment_runner is not runner:
            return {"status": "failed", "reason": "autonomy_fabric_runner_not_canonical"}
        return {"status": "ok", "runner": type(runner).__name__, "executor_configured": True, "job_registered": True, "canonical": True}

    def _economic_feedback(self) -> dict[str, Any]:
        context = self.factory.economic_learning_context()
        required = {"productive_sources", "average_realization_ratio", "daily_realized_eur", "daily_expected_eur", "verified_financial_outcome"}
        missing = sorted(required - set(context))
        if missing:
            return {"status": "failed", "missing": missing}
        if context["daily_realized_eur"] == 0 and context["verified_financial_outcome"]:
            return {"status": "failed", "reason": "verified_without_realized_revenue"}
        return {"status": "ok", "productive_sources": context["productive_sources"], "average_realization_ratio": str(context["average_realization_ratio"])}

    def _knowledge(self) -> dict[str, Any]:
        repository = getattr(self.factory, "knowledge", None)
        if repository is None:
            return {"status": "failed", "configured": False}
        return {"status": "ok", "configured": True, "count": repository.count()}

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
