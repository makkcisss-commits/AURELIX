"""Governed self-development controller for AURELIX."""
from __future__ import annotations
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

def _now() -> str: return datetime.now(timezone.utc).isoformat()

@dataclass(frozen=True)
class ChangePlan:
    id: str
    objective: str
    scope: list[str]
    rationale: str
    validation: list[str]
    status: str = "awaiting_approval"
    created_at: str = ""

class SystemDeveloper:
    """Inspect, plan, validate and execute only bounded repository mutations."""
    approval_required = True
    SAFE_ACTIONS = {"create_file", "update_file", "delete_file"}
    MAX_FILES = 5
    MAX_CONTENT_BYTES = 100_000
    def __init__(self, diagnostics, repository=None) -> None:
        self.diagnostics, self.repository = diagnostics, repository
    def plan(self, objective: str, scope: list[str] | None = None) -> dict[str, Any]:
        objective = objective.strip()
        if not objective: raise ValueError("development objective is required")
        diagnostic = self.diagnostics.run()
        inferred = scope or [f"repair:{x['name']}" for x in diagnostic["checks"] if x["status"] != "ok"] or ["improve:validated_system_capacity"]
        plan = ChangePlan(str(uuid4()), objective, inferred, "Generated from live system state; implementation must pass validation.", ["run self diagnostics", "run relevant tests", "verify integration contracts", "record result"], created_at=_now())
        self.diagnostics.factory.runtime.store.audit("system_developer.plan", "system_developer", "plan_change", "requested", asdict(plan))
        return asdict(plan)
    def approve(self, plan: dict[str, Any], approved: bool) -> dict[str, Any]:
        result = {**plan, "status": "approved" if approved else "rejected"}
        if approved: result["approved_at"] = _now()
        self.diagnostics.factory.runtime.store.audit("system_developer.approved", "owner", "approve_change", "succeeded", {"plan_id": plan.get("id"), "approved": approved})
        return result
    def execute(self, plan: dict[str, Any], *, approved: bool = False) -> dict[str, Any]:
        if not approved or plan.get("status") != "approved": return {"status":"awaiting_approval","plan_id":plan.get("id")}
        if self.repository is None: return {"status":"awaiting_repository_adapter","plan_id":plan.get("id")}
        changes = plan.get("changes") or []
        if not isinstance(changes, list) or not changes or len(changes) > self.MAX_FILES: return {"status":"rejected","reason":"invalid_change_set","plan_id":plan.get("id")}
        results=[]
        for change in changes:
            result=self._apply_change(change); results.append(result)
            if result.get("status") != "applied": return {"status":"failed","plan_id":plan.get("id"),"results":results}
        self.diagnostics.factory.runtime.store.audit("system_developer.executed", "system_developer", "execute_change", "succeeded", {"plan_id":plan.get("id"),"files":len(results)})
        return {"status":"applied","plan_id":plan.get("id"),"results":results}
    def _apply_change(self, change: dict[str, Any]) -> dict[str, Any]:
        action, path = change.get("action"), str(change.get("path",""))
        if action not in self.SAFE_ACTIONS: return {"status":"rejected","reason":"unsupported_action","action":action,"path":path}
        if not self._safe_path(path): return {"status":"rejected","reason":"unsafe_path","path":path}
        content=change.get("content","")
        if action in {"create_file","update_file"} and len(str(content).encode()) > self.MAX_CONTENT_BYTES: return {"status":"rejected","reason":"content_too_large","path":path}
        try:
            if action=="create_file": sha=self.repository.create_file(path,str(content),change.get("message","system developer change"))
            elif action=="update_file": sha=self.repository.update_file(path,str(content),str(change.get("sha","")),change.get("message","system developer change"))
            else: sha=self.repository.delete_file(path,str(change.get("sha","")),change.get("message","system developer change"))
            return {"status":"applied","action":action,"path":path,"commit":sha}
        except Exception as exc: return {"status":"failed","action":action,"path":path,"error":type(exc).__name__}
    @staticmethod
    def _safe_path(path: str) -> bool:
        return bool(path) and not path.startswith("/") and ".." not in path.split("/") and not re.search(r"(^|/)(\.git|\.github)(/|$)",path)
