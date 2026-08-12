from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import uuid4


class ExperimentStatus(str, Enum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class Experiment:
    experiment_id: str
    opportunity_id: str
    objective: str
    sandbox: str
    success_metric: str
    budget_eur: float
    status: ExperimentStatus = ExperimentStatus.PROPOSED


class ExperimentService:
    """Creates bounded experiments; it never executes arbitrary code."""

    def __init__(self) -> None:
        self._items: dict[str, Experiment] = {}

    def propose(self, *, opportunity_id: str, objective: str, sandbox: str,
                success_metric: str, budget_eur: float) -> Experiment:
        if budget_eur < 0:
            raise ValueError("experiment budget cannot be negative")
        item = Experiment(
            experiment_id=str(uuid4()), opportunity_id=opportunity_id,
            objective=objective, sandbox=sandbox,
            success_metric=success_metric, budget_eur=budget_eur,
        )
        self._items[item.experiment_id] = item
        return item

    def get(self, experiment_id: str) -> Experiment:
        return self._items[experiment_id]

    def mark_blocked(self, experiment_id: str) -> Experiment:
        current = self._items[experiment_id]
        updated = Experiment(**{**current.__dict__, "status": ExperimentStatus.BLOCKED})
        self._items[experiment_id] = updated
        return updated

    def mark_completed(self, experiment_id: str) -> Experiment:
        current = self._items[experiment_id]
        updated = Experiment(**{**current.__dict__, "status": ExperimentStatus.COMPLETED})
        self._items[experiment_id] = updated
        return updated
