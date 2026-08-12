"""Evidence-based evaluation for completed experiment measurements."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class EvaluationResult:
    experiment_id: str
    passed: bool
    confidence: float
    metrics: dict[str, float] = field(default_factory=dict)
    reasons: tuple[str, ...] = ()


class EvaluationEngine:
    """Evaluate explicit numeric success criteria without inventing evidence.

    Criteria use a small, auditable syntax: {"metric": "conversion", "operator": ">=", "target": 0.1}.
    Missing measurements fail closed.
    """

    def evaluate(self, experiment_id: str, criteria: list[dict[str, Any]], metrics: Mapping[str, Any]) -> EvaluationResult:
        reasons: list[str] = []
        if not criteria:
            return EvaluationResult(experiment_id, False, 0.0, self._numeric(metrics), ("no success criteria",))
        passed_count = 0
        numeric = self._numeric(metrics)
        for criterion in criteria:
            name = str(criterion.get("metric", ""))
            op = str(criterion.get("operator", ">="))
            target = criterion.get("target")
            if name not in numeric or not isinstance(target, (int, float)):
                reasons.append(f"missing metric or target: {name}")
                continue
            actual = numeric[name]
            ok = {">=": actual >= target, ">": actual > target, "<=": actual <= target, "<": actual < target, "==": actual == target}.get(op)
            if ok is None:
                reasons.append(f"unsupported operator: {op}")
            elif ok:
                passed_count += 1
            else:
                reasons.append(f"criterion failed: {name} {op} {target} (actual={actual})")
        passed = passed_count == len(criteria) and not reasons
        confidence = passed_count / len(criteria)
        return EvaluationResult(experiment_id, passed, confidence, numeric, tuple(reasons))

    @staticmethod
    def _numeric(metrics: Mapping[str, Any]) -> dict[str, float]:
        return {str(k): float(v) for k, v in metrics.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
