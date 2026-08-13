"""Closed-loop governed self-improvement orchestration."""
from __future__ import annotations
from typing import Any
from .recovery import RecoveryController
from .system_validation import SystemValidation
from .learning_feedback import LearningFeedbackLoop

class SelfImprovementController:
    """Connect diagnosis, planning, approval, execution, validation, recovery and learning."""
    def __init__(self, diagnostics, developer) -> None:
        self.diagnostics = diagnostics
        self.developer = developer
        self.recovery = RecoveryController(diagnostics.factory.runtime)
        self.validation = SystemValidation(diagnostics.factory)
        self.learning = LearningFeedbackLoop(diagnostics.factory)

    def assess(self) -> dict[str, Any]:
        report = self.diagnostics.run(); validation = self.validation.run()
        return {"status": validation["status"], "report": report, "validation": validation, "repair_queue": list(report.get("next_actions", []))}

    def prepare(self, objective: str, scope: list[str] | None = None) -> dict[str, Any]:
        before = self.diagnostics.run(); validation = self.validation.run(); plan = self.developer.plan(objective, scope)
        return {"status": "awaiting_approval", "before": before, "validation": validation, "plan": plan}

    def execute_and_verify(self, plan: dict[str, Any], *, approved: bool = False) -> dict[str, Any]:
        before = self.diagnostics.run(); before_validation = self.validation.run()
        if before_validation["status"] == "failed":
            result = {"status": "blocked_precondition", "before": before, "before_validation": before_validation, "execution": None, "after": before, "recovery": None}
            self.learning.record_cycle(event="self_improvement_blocked", outcome="blocked", details=result); return result
        execution = self.developer.execute(plan, approved=approved)
        if execution.get("status") != "applied":
            result = {"status": execution.get("status", "failed"), "before": before, "before_validation": before_validation, "execution": execution, "after": before, "recovery": None}
            self.learning.record_cycle(event="self_improvement_execution", outcome=result["status"], details=result); return result
        after = self.diagnostics.run(); after_validation = self.validation.run(); recovery = self.recovery.decide(before, after, execution)
        regression = recovery["regression"] or after_validation["status"] == "failed"
        status = "verified" if not regression and after_validation["status"] == "ok" else "regression_detected"
        result = {"status": status, "before": before, "before_validation": before_validation, "execution": execution, "after": after, "after_validation": after_validation, "regression": regression, "recovery": recovery}
        self.learning.record_cycle(event="self_improvement_completed", outcome=status, details=result)
        return result
