from decimal import Decimal

from aurelix_core.economic_feedback import EconomicFeedback
from aurelix_core.economic_learning_adapter import EconomicLearningAdapter


def test_economic_learning_exposes_only_observed_outcomes(portfolio, active_source):
    active_source.realized_daily_eur = Decimal("12.50")
    active_source.expected_daily_eur = Decimal("20.00")
    portfolio.add(active_source)

    adapter = EconomicLearningAdapter(EconomicFeedback(portfolio))
    evidence = adapter.evidence()

    assert len(evidence) == 1
    assert evidence[0].observed_daily_eur == Decimal("12.50")
    assert evidence[0].expected_daily_eur == Decimal("20.00")
    assert evidence[0].realization_ratio == Decimal("0.625")


def test_learning_context_cannot_authorize_execution(portfolio, active_source):
    portfolio.add(active_source)
    context = EconomicLearningAdapter(EconomicFeedback(portfolio)).learning_context()

    assert context["verified_financial_outcome"] is True
    assert context["evidence_type"] == "verified_economic_outcome"
    assert context["authority"] == "none"
    assert context["execution_allowed"] is False
