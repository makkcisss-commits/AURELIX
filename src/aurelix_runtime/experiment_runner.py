"""Execution lifecycle for experiments; measurements are injected, never fabricated."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from aurelix_core.evaluation import EvaluationEngine, EvaluationResult
from .integrated_engines import Experiment


@dataclass
class ExperimentRun:
    experiment_id: str
    hypothesis: str
    status: str = "setup"
    observations: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
    evaluation: EvaluationResult | None = None


class ExperimentRunner:
    def __init__(
        self,
        collector: Callable[[Experiment], list[dict[str, Any]]],
        evaluator: EvaluationEngine | None = None,
        on_complete: Callable[[Experiment, ExperimentRun], None] | None = None,
    ):
        self.collector = collector
        self.evaluator = evaluator or EvaluationEngine()
        self.on_complete = on_complete

    def execute(self, experiment: Experiment) -> ExperimentRun:
        if experiment.status == "complete" and experiment.result is not None:
            run = ExperimentRun(experiment.id, experiment.hypothesis, status="complete")
            run.result = None if False else None  # compatibility: result remains on Experiment
            return run

        run = ExperimentRun(experiment.id, experiment.hypothesis)
        run.status = "running"
        observations = self.collector(experiment)
        run.observations = list(observations)

        # Absence of measurement is a real state, never an implicit failure or success.
        if not run.observations:
            run.status = "awaiting_measurement"
            experiment.status = "awaiting_measurement"
            experiment.result = None
            if self.on_complete:
                self.on_complete(experiment, run)
            return run

        run.status = "measuring"
        run.metrics = self.compute_metrics(run.observations)
        if not run.metrics:
            run.status = "awaiting_measurement"
            experiment.status = "awaiting_measurement"
            experiment.result = None
            if self.on_complete:
                self.on_complete(experiment, run)
            return run

        run.status = "evaluation"
        criteria = [c for c in experiment.success_criteria if isinstance(c, dict)]
        run.evaluation = self.evaluator.evaluate(experiment.id, criteria, run.metrics)
        experiment.status = "complete"
        experiment.result = {
            "passed": run.evaluation.passed,
            "confidence": run.evaluation.confidence,
            "metrics": run.metrics,
            "reasons": list(run.evaluation.reasons),
        }
        run.status = "complete"
        if self.on_complete:
            self.on_complete(experiment, run)
        return run

    @staticmethod
    def compute_metrics(observations: list[dict[str, Any]]) -> dict[str, float]:
        values: dict[str, list[float]] = {}
        for observation in observations:
            for key, value in observation.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    values.setdefault(str(key), []).append(float(value))
        return {key: sum(items) / len(items) for key, items in values.items() if items}
