"""Governed self-development planner for AURELIX.

The developer agent can inspect and plan changes, but production mutations are
explicitly gated. It never executes arbitrary model-generated code.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ChangePlan:
    id: str
    objective: str
    scope: list[str]
    rationale: str
    validation: list[str]
    status: str = "awaiting_approval"
    created_at: str = _now()


class SystemDeveloper:
    """Turns diagnostics or owner requests into safe, auditable change plans."""

    approval_required = True

    def __init__(self, diagnostics) -> None:
        self.diagnostics = diagnostics

    def plan(self, objective: str, scope: list[str] | None = None) -> dict[str, Any]:
        objective = objective.strip()
        if not objective:
            raise ValueError("development objective is required")
        diagnostic = self.diagnostics.run()
        inferred_scope = scope or [f"repair:{x['name']}" for x in diagnostic["checks"] if x["status"] != "ok"]
        if not inferred_scope:
            inferred_scope = ["improve:validated_system_capacity"]
        plan = ChangePlan(
            id=str(uuid4()), objective=objective, scope=inferred_scope,
            rationale="Generated from the current system state; implementation must pass validation.",
            validation=["run self diagnostics", "run relevant tests", "verify integration contracts", "record result"],
        )
        self.diagnostics.factory.runtime.store.audit("system_developer.plan", "system_developer", "plan_change", "requested", asdict(plan))
        return asdict(plan)

    def approve(self, plan: dict[str, Any], approved: bool) -> dict[str, Any]:
        if not approved:
            return {**plan, "status": "rejected"}
        result = {**plan, "status": "approved", "approved_at": _now()}
        self.diagnostics.factory.runtime.store.audit("system_developer.approved", "owner", "approve_change", "succeeded", {"plan_id": plan.get("id")})
        return result
