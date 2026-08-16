"""System-wide integrity control plane for AURELIX.

This controller is deliberately additive: EngineFactory, SystemDiagnostics and
SystemValidation remain the existing authorities. The controller observes their
composition and enforces a small set of canonical ownership invariants so a
new implementation cannot silently coexist with an older implementation.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class IntegrityFinding:
    code: str
    status: str
    severity: str
    responsibility: str
    detail: str
    evidence: dict[str, Any]


class SystemIntegrityError(RuntimeError):
    """Raised when a protected canonical-system invariant is violated."""


class SystemIntegrityController:
    """Read-only system control plane for canonical ownership and durable state.

    The controller never invents a replacement and never silently disables an
    implementation. It reports a deterministic finding; a safe replacement
    must be made at the canonical composition root and then revalidated.
    """

    def __init__(self, factory) -> None:
        self.factory = factory

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def run(self) -> dict[str, Any]:
        findings: list[IntegrityFinding] = []
        findings.extend(self._composition_findings())
        findings.extend(self._schedule_findings())
        findings.extend(self._resume_state_findings())
        findings.extend(self._runtime_registration_findings())
        failures = [f for f in findings if f.status == "failed"]
        warnings = [f for f in findings if f.status == "warning"]
        overall = "failed" if failures else "warning" if warnings else "ok"
        return {
            "status": overall,
            "checked_at": self._now(),
            "summary": {
                "total": len(findings),
                "failed": len(failures),
                "warnings": len(warnings),
            },
            "findings": [asdict(f) for f in findings],
        }

    def assert_ready(self) -> dict[str, Any]:
        report = self.run()
        if report["status"] == "failed":
            first = next(f for f in report["findings"] if f["status"] == "failed")
            raise SystemIntegrityError(f"{first['code']}: {first['detail']}")
        return report

    def _composition_findings(self) -> list[IntegrityFinding]:
        f = self.factory
        fabric = getattr(f, "autonomy_fabric", None)
        enterprise = getattr(f, "enterprise", None)
        findings: list[IntegrityFinding] = []
        if not f.config.register_autonomy:
            findings.append(IntegrityFinding("AUTONOMY_DISABLED", "warning", "medium", "autonomy", "autonomy fabric is intentionally disabled", {}))
            return findings
        if fabric is None or enterprise is None:
            return [IntegrityFinding("CANONICAL_COMPOSITION_MISSING", "failed", "critical", "composition", "autonomy is enabled but the canonical fabric/enterprise composition is missing", {"fabric": fabric is not None, "enterprise": enterprise is not None})]
        shared = {
            "research": fabric.research is f.research and enterprise.research is f.research,
            "academy": fabric.academy is f.academy and enterprise.academy is f.academy,
            "knowledge": fabric.knowledge is f.knowledge_engine and enterprise.knowledge_engine is f.knowledge_engine,
            "innovation": fabric.innovation is f.innovation and enterprise.innovation is f.innovation,
            "experiment": fabric.experiment is f.experiment and enterprise.experiment is f.experiment,
            "evaluation": fabric.evaluation is f.evaluation and enterprise.evaluation is f.evaluation,
            "opportunity": fabric.opportunity is f.opportunity and enterprise.opportunity is f.opportunity,
            "business": fabric.business is f.business and enterprise.business is f.business,
            "engine_store": fabric.engines is enterprise.store,
            "message_fabric": fabric.message_fabric is f.message_fabric,
        }
        for responsibility, ok in shared.items():
            if not ok:
                findings.append(IntegrityFinding("DUPLICATE_OR_SPLIT_OWNER", "failed", "critical", responsibility, "canonical responsibility has more than one live owner or a disconnected composition", {"shared": shared}))
        if all(shared.values()):
            findings.append(IntegrityFinding("CANONICAL_OWNERSHIP_OK", "ok", "info", "composition", "all protected runtime responsibilities share the EngineFactory composition", shared))
        return findings

    def _schedule_findings(self) -> list[IntegrityFinding]:
        scheduler = getattr(getattr(self.factory, "runtime", None), "scheduler", None)
        # Scheduler is owned by AurelixSystem, not EngineFactory. Inspect it if
        # the factory exposes a system facade; otherwise this check is optional.
        system = getattr(self.factory, "system", None)
        if scheduler is None and system is None:
            return []
        scheduler = scheduler or getattr(system, "scheduler", None)
        if scheduler is None:
            return []
        schedules = list(getattr(scheduler, "schedules", []))
        names = [str(getattr(item, "name", "")) for item in schedules]
        duplicates = sorted({name for name in names if name and names.count(name) > 1})
        if duplicates:
            return [IntegrityFinding("DUPLICATE_SCHEDULE_IDENTITY", "failed", "high", "scheduler", "the same schedule identity is registered more than once", {"duplicates": duplicates})]
        return [IntegrityFinding("SCHEDULE_IDENTITY_OK", "ok", "info", "scheduler", "schedule identities are unique", {"count": len(schedules)})]

    def _resume_state_findings(self) -> list[IntegrityFinding]:
        store = self.factory.runtime.store
        findings: list[IntegrityFinding] = []
        with store.lock:
            rows = store.db.execute("SELECT key,value FROM runtime_state WHERE key LIKE 'mission-resume:%'").fetchall()
        for row in rows:
            key = str(row["key"])
            try:
                state = json.loads(row["value"])
            except (TypeError, json.JSONDecodeError):
                findings.append(IntegrityFinding("CORRUPT_RESUME_STATE", "failed", "critical", "mission-resume", "resume coordination state is not valid JSON", {"key": key}))
                continue
            phase = state.get("state")
            if phase == "reserved":
                lease = state.get("lease_until")
                if lease is None:
                    findings.append(IntegrityFinding("LEGACY_RESUME_LEASE", "failed", "high", "mission-resume", "reserved resume has no lease metadata and cannot be safely reclaimed", {"key": key}))
                else:
                    try:
                        float(lease)
                    except (TypeError, ValueError):
                        findings.append(IntegrityFinding("INVALID_RESUME_LEASE", "failed", "high", "mission-resume", "reserved resume has invalid lease metadata", {"key": key, "lease_until": lease}))
            elif phase not in {"running", "completed"}:
                findings.append(IntegrityFinding("INVALID_RESUME_STATE", "failed", "high", "mission-resume", "unknown resume coordination state", {"key": key, "state": phase}))
        if not any(f.responsibility == "mission-resume" for f in findings):
            findings.append(IntegrityFinding("RESUME_STATE_OK", "ok", "info", "mission-resume", "all persisted resume coordination records satisfy the state contract", {"records": len(rows)}))
        return findings

    def _runtime_registration_findings(self) -> list[IntegrityFinding]:
        runtime = self.factory.runtime
        claimed = getattr(runtime, "claimed_handlers", {})
        handlers = getattr(runtime, "handlers", {})
        overlaps = sorted(set(claimed).intersection(handlers))
        if overlaps:
            return [IntegrityFinding("AMBIGUOUS_RUNTIME_REGISTRATION", "failed", "critical", "runtime", "a job kind is registered in both normal and claimed handler registries", {"overlaps": overlaps})]
        return [IntegrityFinding("RUNTIME_REGISTRATION_OK", "ok", "info", "runtime", "runtime job registrations have one execution authority", {"claimed": sorted(claimed), "handlers": sorted(handlers)})]
