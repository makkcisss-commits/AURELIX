"""Closed-loop governed self-improvement orchestration."""
from __future__ import annotations

from typing import Any

from .recovery import RecoveryController
from .system_validation import SystemValidation


class SelfImprovementController:
    """Connect diagnosis, planning, approval, execution, validation and recovery."""

    def __init__(self, diagnostics, developer) -> None:
        self.diagnostics = diagnostics
        self.developer = developer
        self.recovery = RecoveryController(diagnostics.factory.runtime)
        self.validation = SystemValidation(diagnostics.factory)

    def assess(self) -> dict[str, Any]:
        report = self.diagnostics.run()
        validation = self.validation.run()
        return {"status": validation["status"], "report": report, "validation": validation, "repair_queue": list(report.get("next_actions", []))}

    def prepare(self, objective: str, scope: list[str] | None = None) -> dict[str, Any]:
        before = self.diagnostics.run()
        validation = self.validation.run()
        plan = self.developer.plan(objective, scope)
        return {"status": "awaiting_approval", "before": before, "validation": validation, "plan": plan}

    def execute_and_verify(self, plan: dict[str, Any], *, approved: bool = False) -> dict[str, Any]:
        before = self.diagnostics.run()
        before_validation = self.validation.run()
        if before_validation["status"] == "failed":
            return {"status": "blocked_precondition", "before": before, "before_validation": before_validation, "execution": None, "after": before, "recovery": None}
        execution = self.developer.execute(plan, approved=approved)
        if execution.get("status") != "applied":
            return {"status": execution.get("status", "failed"), "before": before, "before_validation": before_validation, "execution": execution, "after": before, "recovery": None}
        after = self.diagnostics.run()
        after_validation = self.validation.run()
        recovery = self.recovery.decide(before, after, execution)
        regression = recovery["regression"] or after_validation["status"] == "failed"
        status = "verified" if not regression and after_validation["status"] == "ok" else "regression_detected"
        return {"status": status, "before": before, "before_validation": before_validation, "execution": execution, "after": after, "after_validation": after_validation, "regression": regression, "recovery": recovery}
