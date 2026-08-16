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
    """Runs bounded checks across the real composition, not just object presence."""

    def __init__(self, factory) -> None:
        self.factory = factory

    def run(self) -> dict[str, Any]:
        checks: list[DiagnosticCheck] = [
            self._check("runtime", self._runtime),
            self._check("canonical_composition", self._canonical_composition),
            self._check("system_integrity", self._system_integrity),
            self._check("experiment_execution", self._experiment_execution),
            self._check("economic_feedback", self._economic_feedback),
            self._check("live_opportunity_readiness", self._live_opportunity_readiness),
            self._check("model_provider", lambda: self._provider("model_provider")),
            self._check("research_provider", lambda: self._provider("research_provider")),
            self._check("knowledge_store", self._knowledge),
            self._check("enterprise_loop", self._enterprise_loop),
            self._check("developer_control", self._developer_control),
        ]
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

    def _canonical_composition(self) -> DiagnosticCheck:
        fabric = getattr(self.factory, "autonomy_fabric", None)
        enterprise = getattr(self.factory, "enterprise", None)
        if self.factory.config.register_autonomy and (fabric is None or enterprise is None):
            return DiagnosticCheck("canonical_composition", "failed", "high", "autonomy is enabled without a canonical shared fabric", {})
        if fabric is None:
            return DiagnosticCheck("canonical_composition", "degraded", "medium", "autonomy fabric is disabled", {"enabled": False})
        shared_engines = {
            "research": fabric.research is self.factory.research,
            "academy": fabric.academy is self.factory.academy,
            "knowledge": fabric.knowledge is self.factory.knowledge_engine,
            "innovation": fabric.innovation is self.factory.innovation,
            "experiment": fabric.experiment is self.factory.experiment,
            "evaluation": fabric.evaluation is self.factory.evaluation,
            "opportunity": fabric.opportunity is self.factory.opportunity,
            "business": fabric.business is self.factory.business,
            "engine_store": fabric.engines is enterprise.store,
            "message_fabric": fabric.message_fabric is self.factory.message_fabric,
        }
        if not all(shared_engines.values()):
            return DiagnosticCheck("canonical_composition", "failed", "high", "multiple composition instances detected", shared_engines)
        return DiagnosticCheck("canonical_composition", "ok", "info", "runtime autonomy and enterprise loop share one composition", shared_engines)

    def _system_integrity(self) -> DiagnosticCheck:
        controller = getattr(self.factory, "integrity", None)
        if controller is None:
            return DiagnosticCheck("system_integrity", "failed", "critical", "system integrity control plane is not composed", {})
        report = controller.run()
        status = "failed" if report["status"] == "failed" else "degraded" if report["status"] == "warning" else "ok"
        severity = "critical" if status == "failed" else "medium" if status == "degraded" else "info"
        return DiagnosticCheck("system_integrity", status, severity, "canonical ownership and durable-state integrity was inspected", report)

    def _experiment_execution(self) -> DiagnosticCheck:
        executor = getattr(self.factory, "experiment_executor", None)
        runner = getattr(self.factory, "experiment_runner", None)
        submitter = getattr(getattr(self.factory, "enterprise", None), "experiment_submitter", None)
        if executor is None or runner is None or submitter is None:
            return DiagnosticCheck(
                "experiment_execution", "failed", "high",
                "durable experiment execution is not mounted; experiments must not be evaluated as if executed",
                {"executor": executor is not None, "runner": runner is not None, "submitter": submitter is not None},
            )
        return DiagnosticCheck(
            "experiment_execution", "ok", "info",
            "experiment proposals are mounted onto the durable runtime execution path",
            {"executor": type(executor).__name__, "runner": type(runner).__name__, "durable_job_kind": "experiment.run"},
        )

    def _economic_feedback(self) -> DiagnosticCheck:
        context = self.factory.economic_learning_context()
        required = {"productive_sources", "average_realization_ratio", "daily_realized_eur", "daily_expected_eur", "verified_financial_outcome"}
        missing = sorted(required - set(context))
        if missing:
            return DiagnosticCheck("economic_feedback", "failed", "high", "economic feedback is missing ranking fields", {"missing": missing})
        if context["daily_realized_eur"] == 0 and context["verified_financial_outcome"]:
            return DiagnosticCheck("economic_feedback", "failed", "high", "financial evidence is marked verified without realized revenue", context)
        return DiagnosticCheck("economic_feedback", "ok", "info", "economic feedback is explicit and realization-aware", {
            "productive_sources": context["productive_sources"],
            "average_realization_ratio": str(context["average_realization_ratio"]),
            "verified_financial_outcome": context["verified_financial_outcome"],
        })

    def _live_opportunity_readiness(self) -> DiagnosticCheck:
        mode = __import__("os").environ.get("AURELIX_MODE", "production").strip().lower()
        provider = getattr(self.factory, "research_provider", None)
        if mode == "development":
            return DiagnosticCheck("live_opportunity_readiness", "degraded", "medium", "development mode uses synthetic evidence; live opportunity discovery is not enabled", {"mode": mode, "provider": type(provider).__name__ if provider else None, "real_evidence": False})
        if provider is None:
            return DiagnosticCheck("live_opportunity_readiness", "failed", "high", "no live research provider is configured; real opportunity discovery cannot run", {"mode": mode, "real_evidence": False})
        return DiagnosticCheck("live_opportunity_readiness", "ok", "info", "live research provider is configured; evidence still requires qualification before economic execution", {"mode": mode, "provider": type(provider).__name__, "real_evidence": True})

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
