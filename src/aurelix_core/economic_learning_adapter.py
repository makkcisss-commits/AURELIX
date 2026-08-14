"""Bridge realized economic outcomes into bounded learning evidence."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .economic_feedback import EconomicFeedback


@dataclass(frozen=True)
class EconomicLearningEvidence:
    source_id: str
    observed_daily_eur: Decimal
    expected_daily_eur: Decimal
    realization_ratio: Decimal
    productive: bool


class EconomicLearningAdapter:
    """Expose verified economic outcomes as learning evidence, never authority."""

    def __init__(self, feedback: EconomicFeedback) -> None:
        self.feedback = feedback

    def evidence(self) -> list[EconomicLearningEvidence]:
        snapshot = self.feedback.snapshot()
        return [
            EconomicLearningEvidence(
                source_id=signal["source_id"],
                observed_daily_eur=Decimal(signal["observed_daily_eur"]),
                expected_daily_eur=Decimal(signal["expected_daily_eur"]),
                realization_ratio=Decimal(signal["realization_ratio"]),
                productive=bool(signal["productive"]),
            )
            for signal in snapshot["signals"]
        ]

    def learning_context(self) -> dict[str, Any]:
        context = self.feedback.learning_context()
        return {
            **context,
            "evidence_type": "verified_economic_outcome",
            "authority": "none",
            "execution_allowed": False,
        }
