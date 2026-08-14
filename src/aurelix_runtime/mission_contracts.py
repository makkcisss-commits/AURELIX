"""Structured mission contracts for the autonomous economic operating loop."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

class MissionState(str, Enum):
    PROPOSED = "proposed"
    PLANNED = "planned"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass(frozen=True)
class MissionTask:
    name: str
    owner: str
    purpose: str
    depends_on: tuple[str, ...] = ()
    evidence_required: tuple[str, ...] = ()

@dataclass
class EconomicMission:
    objective: str
    priority: int = 50
    source: str = "autonomous"
    mission_id: str = field(default_factory=lambda: str(uuid4()))
    state: MissionState = MissionState.PROPOSED
    tasks: list[MissionTask] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    expected_revenue_eur_day: float | None = None

    def plan(self, tasks: list[MissionTask]) -> None:
        if not self.objective.strip():
            raise ValueError("mission objective is required")
        names = {task.name for task in tasks}
        for task in tasks:
            missing = set(task.depends_on) - names
            if missing:
                raise ValueError(f"unknown task dependencies: {sorted(missing)}")
        self.tasks = tasks
        self.state = MissionState.PLANNED

    def start(self) -> None:
        if self.state is not MissionState.PLANNED:
            raise ValueError("mission must be planned before starting")
        self.state = MissionState.RUNNING

    def block(self, reason: str) -> None:
        self.constraints.setdefault("blocked_reasons", []).append(reason)
        self.state = MissionState.BLOCKED

    def complete(self, evidence: list[dict[str, Any]]) -> None:
        if not evidence:
            raise ValueError("completion requires evidence")
        self.evidence.extend(evidence)
        self.state = MissionState.COMPLETED

DEFAULT_ECONOMIC_TASKS = [
    MissionTask("research", "research", "collect and verify external market evidence", evidence_required=("source",)),
    MissionTask("opportunity", "opportunity", "identify concrete opportunities supported by evidence", depends_on=("research",), evidence_required=("opportunity",)),
    MissionTask("business", "business", "qualify a real business or collaboration", depends_on=("opportunity",), evidence_required=("prospect", "need")),
    MissionTask("monetization", "monetization", "model a realistic revenue path", depends_on=("business",), evidence_required=("economics",)),
    MissionTask("validation", "validation", "validate the opportunity before proposing action", depends_on=("monetization",), evidence_required=("validation",)),
]
