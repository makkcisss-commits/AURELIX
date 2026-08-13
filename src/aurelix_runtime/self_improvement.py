"""Closed-loop governed self-improvement orchestration."""
from __future__ import annotations

from typing import Any


class SelfImprovementController:
    """Connect diagnosis, planning, approval, execution and post-change verification."""

    def __init__(self, diagnostics, developer) -> None:
        self.diagnostics = diagnostics
        self.developer = developer

    def assess(self) -> dict[str, Any]:
        report = self.diagnostics.run()
        return {
            "status": report["status"],
            "report": report,
            "repair_queue": list(report.get("next_actions", [])),
        }

    def prepare(self, objective: str, scope: list[str] | None = None) -> dict[str, Any]:
        before = self.diagnostics.run()
        plan = self.developer.plan(objective, scope)
        return {"status": "awaiting_approval", "before": before, "plan": plan}

    def execute_and_verify(self, plan: dict[str, Any], *, approved: bool = False) -> dict[str, Any]:
        before = self.diagnostics.run()
        execution = self.developer.execute(plan, approved=approved)
        if execution.get("status") != "applied":
            return {"status": execution.get("status", "failed"), "before": before, "execution": execution, "after": before}
        after = self.diagnostics.run()
        return {
            "status": "verified" if after["status"] in {"ok", "degraded"} else "regression_detected",
            "before": before,
            "execution": execution,
            "after": after,
            "regression": before["summary"]["failed"] < after["summary"]["failed"],
        }
