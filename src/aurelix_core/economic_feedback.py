"""Economic feedback loop connecting learning, opportunities and realized revenue."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class EconomicSignal:
    source_id: str
    observed_daily_eur: Decimal
    expected_daily_eur: Decimal
    realization_ratio: Decimal
    productive: bool


class EconomicFeedback:
    """Converts observed revenue into bounded signals for future decisions.

    It never turns estimates into realized revenue and never authorizes a business
    action by itself. It provides evidence for the next opportunity-ranking cycle.
    """

    def __init__(self, portfolio) -> None:
        self.portfolio = portfolio

    def snapshot(self) -> dict[str, Any]:
        sources = self.portfolio.all()
        signals = [self._signal(s) for s in sources]
        productive = [s for s in signals if s.productive]
        realized = sum((s.observed_daily_eur for s in signals), Decimal("0"))
        expected = sum((s.expected_daily_eur for s in signals), Decimal("0"))
        return {
            "sources": len(sources),
            "productive_sources": len(productive),
            "daily_realized_eur": realized,
            "daily_expected_eur": expected,
            "realization_ratio": (realized / expected if expected > 0 else Decimal("0")),
            "signals": [s.__dict__ for s in signals],
        }

    @staticmethod
    def _signal(source) -> EconomicSignal:
        expected = Decimal(source.expected_daily_eur)
        observed = Decimal(source.realized_daily_eur)
        ratio = observed / expected if expected > 0 else Decimal("0")
        return EconomicSignal(
            source_id=source.source_id,
            observed_daily_eur=observed,
            expected_daily_eur=expected,
            realization_ratio=ratio,
            productive=bool(source.status.value == "active" and observed > 0),
        )

    def learning_context(self) -> dict[str, Any]:
        snap = self.snapshot()
        return {
            "objective": "economic performance feedback",
            "verified_financial_outcome": True,
            "portfolio": snap,
            "rule": "only realized revenue is financial evidence; forecasts remain forecasts",
        }
