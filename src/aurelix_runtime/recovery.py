"""Recovery policy for self-improvement changes."""
from __future__ import annotations
from typing import Any


class RecoveryController:
    """Decides whether a failed improvement should be held, rolled back, or accepted."""

    def __init__(self, runtime) -> None:
        self.runtime = runtime

    def decide(self, before: dict[str, Any], after: dict[str, Any], execution: dict[str, Any]) -> dict[str, Any]:
        before_failed = before.get("summary", {}).get("failed", 0)
        after_failed = after.get("summary", {}).get("failed", 0)
        regression = after_failed > before_failed or after.get("status") == "failed"
        decision = "rollback_required" if regression else "accepted"
        self.runtime.store.audit(
            "self_improvement.recovery",
            "recovery",
            "evaluate_change",
            "failed" if regression else "succeeded",
            {"decision": decision, "before_failed": before_failed, "after_failed": after_failed,
             "execution_status": execution.get("status")},
        )
        return {"decision": decision, "regression": regression, "before_failed": before_failed, "after_failed": after_failed}
