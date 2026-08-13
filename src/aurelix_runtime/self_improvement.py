"""Closed-loop governed self-improvement orchestration."""
from __future__ import annotations

from typing import Any

from .recovery import RecoveryController


class SelfImprovementController:
    """Connect diagnosis, planning, approval, execution, verification and recovery."""

    def __init__(self, diagnostics, developer) -> None:
        self.diagnostics = diagnostics
        self.developer = developer
        self.recovery = RecoveryController(diagnostics.factory.runtime)

    def assess(self) -> dict[str, Any]:
        report = self.diagnostics.run()
        return {"status": report["status"], "report": report, "repair_queue": list(report.get("next_actions", []))}

    def prepare(self, objective: str, scope: list[str] | None = None) -> dict[str, Any]:
        before = self.diagnostics.run()
        plan = self.developer.plan(objective, scope)
        return {"status": "awaiting_approval", "before": before, "plan": plan}

    def execute_and_verify(self, plan: dict[str, Any], *, approved: bool = False) -> dict[str, Any]:
        before = self.diagnostics.run()
        execution = self.developer.execute(plan, approved=approved)
        if execution.get("status") != "applied":
            return {"status": execution.get("status", "failed"), "before": before, "execution": execution, "after": before, "recovery": None}
        after = self.diagnostics.run()
        recovery = self.recovery.decide(before, after, execution)
        status = "verified" if recovery["decision"] == "accepted" else "regression_detected"
        return {"status": status, "before": before, "execution": execution, "after": after, "regression": recovery["regression"], "recovery": recovery}
