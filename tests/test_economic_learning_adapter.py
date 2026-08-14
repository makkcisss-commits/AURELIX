from decimal import Decimal
from types import SimpleNamespace

from aurelix_core.economic_feedback import EconomicFeedback
from aurelix_core.economic_learning_adapter import EconomicLearningAdapter


class InMemoryPortfolio:
    def __init__(self, sources):
        self._sources = list(sources)

    def add(self, source):
        self._sources.append(source)

    def all(self):
        return list(self._sources)


def make_source(*, observed="12.50", expected="20.00", active=True):
    return SimpleNamespace(
        source_id="activity-1",
        realized_daily_eur=Decimal(observed),
        expected_daily_eur=Decimal(expected),
        status=SimpleNamespace(value="active" if active else "paused"),
    )


def test_economic_learning_exposes_only_observed_outcomes():
    portfolio = InMemoryPortfolio([])
    portfolio.add(make_source())

    adapter = EconomicLearningAdapter(EconomicFeedback(portfolio))
    evidence = adapter.evidence()

    assert len(evidence) == 1
    assert evidence[0].observed_daily_eur == Decimal("12.50")
    assert evidence[0].expected_daily_eur == Decimal("20.00")
    assert evidence[0].realization_ratio == Decimal("0.625")


def test_learning_context_cannot_authorize_execution():
    portfolio = InMemoryPortfolio([make_source()])
    context = EconomicLearningAdapter(EconomicFeedback(portfolio)).learning_context()

    assert context["verified_financial_outcome"] is True
    assert context["evidence_type"] == "verified_economic_outcome"
    assert context["authority"] == "none"
    assert context["execution_allowed"] is False
